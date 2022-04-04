# -*- coding: utf-8 -*-
import copy
import functools
from typing import Sequence

from pyos import db
from pyos import fs
from pyos import glob
from pyos import os
from pyos import pathlib

__all__ = ('parse_args',)


@functools.singledispatch
def parse_arg(arg) -> Sequence:
    # Maybe it can be turned into an object id
    obj_id = db.to_obj_id(arg)
    if obj_id is not None:
        return (obj_id,)

    raise TypeError(f"Unknown type '{arg}'")


@parse_arg.register(fs.ObjectNode)
def _(arg: fs.ObjectNode):
    return [copy.copy(arg)]


@parse_arg.register(fs.DirectoryNode)
def _(arg: fs.DirectoryNode):
    return [copy.copy(arg)]


@parse_arg.register(fs.ResultsNode)
def _(arg: fs.ResultsNode):
    return parse_args(*arg.children)


@parse_arg.register(os.PathLike)
def _(arg: os.PathLike):
    return [arg]


@parse_arg.register(str)
def _(arg: str):
    obj_id = db.to_obj_id(arg)
    if obj_id is not None:
        return (obj_id,)

    if glob.has_magic(arg):
        return tuple(map(pathlib.PurePath, glob.glob(arg)))

    if isinstance(arg, str):
        # Assume it's a path
        return (pathlib.PurePath(arg),)

    raise TypeError(f"Unknown type '{arg}'")


def parse_args(*args) -> Sequence:
    parsed = []
    for arg in args:
        parsed.extend(parse_arg(arg))

    return parsed
