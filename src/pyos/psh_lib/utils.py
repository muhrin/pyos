import copy
import functools
from typing import TYPE_CHECKING, Sequence

import mincepy

from .. import _globals, fs, glob, os, pathlib

if TYPE_CHECKING:
    import pyos

__all__ = ("parse_fs_entry", "gather_obj_ids")


@functools.singledispatch
def parse_arg(arg) -> Sequence:
    # Anything else could be a (saved) object or an object id
    obj_id = _globals.get_global_session().historian.to_obj_id(arg)
    if obj_id is not None:
        return [fs.ObjectNode(obj_id, path=None)]

    raise TypeError(f"Unknown type '{arg.__class__.__name__}'")


@parse_arg.register(fs.ObjectNode)
def _(arg: "pyos.fs.ObjectNode"):
    return [copy.copy(arg)]


@parse_arg.register(fs.DirectoryNode)
def _(arg: "pyos.fs.DirectoryNode"):
    return [copy.copy(arg)]


@parse_arg.register(fs.ResultsNode)
@parse_arg.register(fs.nodes.FrozenResultsNode)
def _(arg: "pyos.fs.ResultsNode | pyos.fs.nodes.FrozenResultsNode"):
    return parse_fs_entry(*arg.children)


@parse_arg.register(os.PathLike)
def _(arg: "pyos.os.PathLike"):
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
    """Parse objects that can be interpreted as filesystem entries.
    This can be a path, or a filesystem node."""
    parsed = []
    for arg in args:
        parsed.extend(parse_arg(arg))

    return parsed


def gather_obj_ids(entries, historian: mincepy.Historian) -> tuple[list, list]:
    obj_ids = []
    rest = []
    for entry in entries:
        obj_id = historian.to_obj_id(entry)
        if obj_id is not None:
            obj_ids.append(obj_id)
        else:
            rest.append(entry)

    return obj_ids, rest
