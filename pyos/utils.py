import copy
import typing

import mincepy

from . import constants
from . import dirs
from . import nodes


def parse_args(*args) -> typing.Sequence:
    parsed = []
    hist = mincepy.get_historian()
    for arg in args:
        if arg is None:
            parsed.append(None)
        elif isinstance(arg, nodes.ObjectNode):
            parsed.append(copy.copy(arg))
        elif isinstance(arg, nodes.DirectoryNode):
            parsed.append(copy.copy(arg))
        elif isinstance(arg, nodes.ResultsNode):
            parsed.extend(parse_args(*arg.children))
        elif isinstance(arg, dirs.PyosPath):
            parsed.append(arg)
        elif hist.is_obj_id(arg):
            parsed.append(arg)
        else:
            try:
                # Maybe it's an object id
                parsed.append(hist._ensure_obj_id(arg))
                continue
            except mincepy.NotFound:
                pass

            # Maybe it's a live object
            obj_id = hist.get_obj_id(arg)
            if obj_id is not None:
                parsed.append(obj_id)
            elif isinstance(arg, str):
                # Assume it's a path
                parsed.append(dirs.PyosPath(arg))
            else:
                raise TypeError("Unknown type '{}'".format(arg))

    return parsed


def new_meta(orig: dict, new: dict) -> dict:
    merged = new.copy()
    if not orig:
        return merged

    for name in constants.KEYS:
        if name in orig:
            if name.startswith('_'):
                # Always take internal, i.e. underscored, keys
                merged[name] = orig[name]
            else:
                merged.setdefault(name, orig[name])

    return merged
