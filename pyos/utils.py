import typing

import mincepy

from . import dirs
from . import nodes


def parse_args(*args) -> typing.Sequence:
    parsed = []
    hist = mincepy.get_historian()
    for arg in args:
        if isinstance(arg, nodes.ObjectNode):
            parsed.append(arg.obj_id)
            continue

        if isinstance(arg, nodes.DirectoryNode):
            parsed.append(arg.abspath)
            continue

        if isinstance(arg, nodes.ResultsNode):
            parsed.extend(parse_args(*arg.children))
            continue

        if hist.is_obj_id(arg):
            parsed.append(arg)
            continue

        try:
            parsed.append(hist._ensure_obj_id(arg))
            continue
        except mincepy.NotFound:
            pass

        if isinstance(arg, str):
            # Assume it's a path
            parsed.append(dirs.PyosPath(arg))
            continue

        parsed.append(TypeError("Unknown type '{}'".format(arg)))

    return parsed
