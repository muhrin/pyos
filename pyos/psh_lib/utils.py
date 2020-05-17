import copy
import functools
import os
from typing import Sequence

import pyos

__all__ = 'get_terminal_width', 'parse_args'


def get_terminal_width() -> int:
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 100


@functools.singledispatch
def parse_arg(arg) -> Sequence:
    # Maybe it can be turned into an object id
    obj_id = pyos.db.to_obj_id(arg)
    if obj_id is not None:
        return (obj_id,)

    raise TypeError("Unknown type '{}'".format(arg))


@parse_arg.register(pyos.fs.ObjectNode)
def _(arg: pyos.fs.ObjectNode):
    return [copy.copy(arg)]


@parse_arg.register(pyos.fs.DirectoryNode)
def _(arg: pyos.fs.DirectoryNode):
    return [copy.copy(arg)]


@parse_arg.register(pyos.fs.ResultsNode)
def _(arg: pyos.fs.ResultsNode):
    return parse_args(*arg.children)


@parse_arg.register(pyos.os.PathLike)
def _(arg: pyos.os.PathLike):
    return [arg]


@parse_arg.register(str)
def _(arg: str):
    obj_id = pyos.db.to_obj_id(arg)
    if obj_id is not None:
        return (obj_id,)

    if isinstance(arg, str):
        # Assume it's a path
        return (pyos.pathlib.Path(arg),)

    raise TypeError("Unknown type '{}'".format(arg))


def parse_args(*args) -> Sequence:
    parsed = []
    for arg in args:
        parsed.extend(parse_arg(arg))

    return parsed
