import copy
import os
from typing import Sequence

import mincepy

import pyos

__all__ = 'get_terminal_width', 'parse_args'


def get_terminal_width() -> int:
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 100


def parse_args(*args) -> Sequence:
    parsed = []
    hist = mincepy.get_historian()
    for arg in args:
        if arg is None:
            parsed.append(None)
        elif isinstance(arg, pyos.fs.ObjectNode):
            parsed.append(copy.copy(arg))
        elif isinstance(arg, pyos.fs.DirectoryNode):
            parsed.append(copy.copy(arg))
        elif isinstance(arg, pyos.fs.ResultsNode):
            parsed.extend(parse_args(*arg.children))
        elif isinstance(arg, pyos.PyosPath):
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
                parsed.append(pyos.PyosPath(arg))
            else:
                raise TypeError("Unknown type '{}'".format(arg))

    return parsed
