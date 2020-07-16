import re
import inspect
import itertools as it

from manimlib.constants import *


def get_all_descendent_classes(Class):
    awaiting_review = [Class]
    result = []
    while awaiting_review:
        Child = awaiting_review.pop()
        awaiting_review += Child.__subclasses__()
        result.append(Child)
    return result


def filtered_locals(caller_locals):
    result = caller_locals.copy()
    ignored_local_args = ["self", "kwargs"]
    for arg in ignored_local_args:
        result.pop(arg, caller_locals)
    return result

def change_by_dot(dictionary, key, value):
    """Access the dict value by dot key and change it to `value` Example:
    dot_access({"a":0},        "a",   ..) refers to d["a"]
    dot_access({"a":{"b":0}}}, "a.b", ..) refers to d["a"]["b"]
    """
    print("changing")
    nested = key.split(".")

    def replacer(dict_slice, value, key_slice, *rest_slices):
        # if current key_slice is the last, rest_slices evaluates to None
        if not rest_slices:
            dict_slice[key_slice] = value
        else:
            replacer(dict_slice[key_slice], value, *rest_slices)

    # recursively dive into dict, and if key was found in current nested item,
    # change its value
    replacer(dictionary, value, *key.split("."))

def assign_presets(obj):
    """Sets CONFIG values of the given class as given in presets file in
    manimlib/presets.conf.
    """

    class_name = obj.__class__.__name__
    if class_name not in PRESETS.sections():
        return

    # value parsers for different types should take two parameters:
    # class name and option name and return the legit value for that property
    value_parsers = {
        "int": int,
        "bool": lambda value: value.lower() in ["yes", "true", "1", "on"],
        "str": str,
        "const": lambda name: globals()[name]
    }

    for option in PRESETS.options(class_name):

        if not option:
            continue
        # findall is guaranteed to match at least one symbol, so unpacking
        # is safe.
        prop_name, prop_type = re.findall(
            r"([\w\d\.]+)(?: is (\w+))?",
            option
        )[0]
        change_by_dot(
            obj.CONFIG, prop_name,
            value_parsers[prop_type or str](PRESETS.get(class_name, option))
        )


def digest_config(obj, kwargs, caller_locals={}):
    """
    Sets init args and CONFIG values as local variables

    The purpose of this function is to ensure that all
    configuration of any object is inheritable, able to
    be easily passed into instantiation, and is attached
    as an attribute of the object.
    """

    # Assemble list of CONFIGs from all super classes
    classes_in_hierarchy = [obj.__class__]
    static_configs = []
    while len(classes_in_hierarchy) > 0:
        Class = classes_in_hierarchy.pop()
        classes_in_hierarchy += Class.__bases__
        if hasattr(Class, "CONFIG"):
            static_configs.append(Class.CONFIG)

    # Order matters a lot here, first dicts have higher priority
    caller_locals = filtered_locals(caller_locals)
    all_dicts = [kwargs, caller_locals, obj.__dict__]
    all_dicts += static_configs
    obj.__dict__ = merge_dicts_recursively(*reversed(all_dicts))


def merge_dicts_recursively(*dicts):
    """
    Creates a dict whose keyset is the union of all the
    input dictionaries.  The value for each key is based
    on the first dict in the list with that key.

    dicts later in the list have higher priority

    When values are dictionaries, it is applied recursively
    """
    result = dict()
    all_items = it.chain(*[d.items() for d in dicts])
    for key, value in all_items:
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts_recursively(result[key], value)
        else:
            result[key] = value
    return result


def soft_dict_update(d1, d2):
    """
    Adds key values pairs of d2 to d1 only when d1 doesn't
    already have that key
    """
    for key, value in list(d2.items()):
        if key not in d1:
            d1[key] = value


def digest_locals(obj, keys=None):
    caller_locals = filtered_locals(
        inspect.currentframe().f_back.f_locals
    )
    if keys is None:
        keys = list(caller_locals.keys())
    for key in keys:
        setattr(obj, key, caller_locals[key])

# Occasionally convenient in order to write dict.x instead of more laborious
# (and less in keeping with all other attr accesses) dict["x"]


class DictAsObject(object):
    def __init__(self, dict):
        self.__dict__ = dict
