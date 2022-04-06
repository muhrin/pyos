# -*- coding: utf-8 -*-
import copy
import functools
from typing import Sequence, List, Tuple

import mincepy

from pyos import fs
from pyos import glob
from pyos import os
from pyos import pathlib

__all__ = ('parse_fs_entry', 'gather_obj_ids')


@functools.singledispatch
def parse_arg(arg) -> Sequence:
    raise TypeError(f"Unknown type '{arg.__class__.__name__}'")


@parse_arg.register(fs.ObjectNode)
def _(arg: fs.ObjectNode):
    return [copy.copy(arg)]


@parse_arg.register(fs.DirectoryNode)
def _(arg: fs.DirectoryNode):
    return [copy.copy(arg)]


@parse_arg.register(fs.ResultsNode)
def _(arg: fs.ResultsNode):
    return parse_fs_entry(*arg.children)


@parse_arg.register(os.PathLike)
def _(arg: os.PathLike):
    return [arg]


@parse_arg.register(str)
def _(arg: str):
    if glob.has_magic(arg):
        return tuple(map(pathlib.PurePath, glob.glob(arg)))

    if isinstance(arg, str):
        # Assume it's a path
        return (pathlib.PurePath(arg),)

    raise TypeError(f"Unknown type '{arg}'")


def parse_fs_entry(*args) -> Sequence:
    """Parse objects that can be interpreted as filesystem entries.  This can be a path, or a filesystem node."""
    parsed = []
    for arg in args:
        parsed.extend(parse_arg(arg))

    return parsed


def gather_obj_ids(entries, historian: mincepy.Historian) -> Tuple[List, List]:
    obj_ids = []
    rest = []
    for entry in entries:
        obj_id = historian.to_obj_id(entry)
        if obj_id is not None:
            obj_ids.append(obj_id)
        else:
            rest.append(entry)

    return obj_ids, rest
