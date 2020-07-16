import os
import hashlib
from pathlib import Path

import manimlib.constants as consts


def clear_tex_cache(config):
    """Clear TEX_DIR path. May be useful in debugging or if you managed to
    change .tex files there.
    """

    if not config["clear_tex_cache"]:
        return

    for fname in os.listdir(consts.TEX_DIR):
        fpath = os.path.join(consts.TEX_DIR, fname)
        # user will see OSError here in case of some problems
        if os.path.isfile(fpath):
            os.unlink(fpath)


def tex_hash(expression, template_tex_file_body):
    id_str = str(expression + template_tex_file_body)
    hasher = hashlib.sha256()
    hasher.update(id_str.encode())
    # Truncating at 16 bytes for cleanliness
    return hasher.hexdigest()[:16]


def tex_to_svg_file(expression, template_tex_file_body):
    tex_file = generate_tex_file(expression, template_tex_file_body)
    dvi_file = tex_to_dvi(tex_file)
    return dvi_to_svg(dvi_file)


def generate_tex_file(expression, template_tex_file_body):
    result = os.path.join(
        consts.TEX_DIR,
        tex_hash(expression, template_tex_file_body)
    ) + ".tex"
    if not os.path.exists(result):
        print("Writing \"%s\" to %s" % (
            "".join(expression), result
        ))
        with open(result, "w", encoding="utf-8") as outfile:
            outfile.write(template_tex_file_body)
    return result


def tex_to_dvi(tex_file):
    result = tex_file.replace(".tex", ".xdv")
    result = Path(result).as_posix()
    tex_file = Path(tex_file).as_posix()
    tex_dir = Path(consts.TEX_DIR).as_posix()
    if not os.path.exists(result):
        exit_code = os.system(" ".join([
            # executing commands
            "xelatex",
            "-no-pdf",
            "-interaction=batchmode",
            "-halt-on-error",
            "-output-directory=\"{}\"".format(tex_dir),
            "\"{}\"".format(tex_file),
            ">",
            os.devnull
        ]))
        if exit_code != 0:
            log_file = tex_file.replace(".tex", ".log")
            raise Exception(
                "Xelatex error converting to xdv. " +
                "See log output above or the log file: %s" % log_file)
    return result


def dvi_to_svg(dvi_file, regen_if_exists=False):
    """
    Converts a dvi, which potentially has multiple slides, into a
    directory full of enumerated pngs corresponding with these slides.
    Returns a list of PIL Image objects for these images sorted as they
    where in the dvi
    """
    result = dvi_file.replace(".xdv", ".svg")
    result = Path(result).as_posix()
    dvi_file = Path(dvi_file).as_posix()
    if not os.path.exists(result):
        commands = [
            "dvisvgm",
            "\"{}\"".format(dvi_file),
            "-n",
            "-v",
            "0",
            "-o",
            "\"{}\"".format(result),
            ">",
            os.devnull
        ]
        os.system(" ".join(commands))
    return result
