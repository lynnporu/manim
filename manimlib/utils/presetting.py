import re

from manimlib.constants import *


class Presettable:
    """Abstract class for classes which CONFIG may be preseted.
    """
    CONFIG = {}
    CONFIGURATED = False

    def __new__(cls, *args, **kwargs):
        if not cls.CONFIGURATED:
            assign_presets(cls)
            cls.CONFIGURATED = True
        return object.__new__(cls, *args, **kwargs)


def change_by_dot(dictionary, key, value):
    """Access the dict value by dot key and change it to `value` Example:
    dot_access({"a":0},        "a",   ..) refers to d["a"]
    dot_access({"a":{"b":0}}}, "a.b", ..) refers to d["a"]["b"]
    """

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
    """Sets CONFIG values of the UNINSTANTIATED class as given in presets file
    in manimlib/presets.conf.
    """

    class_name = obj.__name__
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
