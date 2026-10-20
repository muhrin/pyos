"""The locate command"""

import argparse
from typing import TYPE_CHECKING, Optional, Sequence, Union

import cmd2

from ... import _globals, db, fs, os, pathlib, psh_lib
from ... import results as results_

if TYPE_CHECKING:
    import pyos


@psh_lib.command()
def locate(
    *obj_or_ids,
) -> Optional[Union[pathlib.Path, Sequence[pathlib.Path]]]:
    """Locate the directory of one or more objects"""
    if not obj_or_ids:
        return None

    session = _globals.get_global_session()
    obj_ids = _get_obj_ids(obj_or_ids, session)

    # Convert to abspaths
    def to_path(fs_path):
        return pathlib.Path(os.withdb.from_fs_path(fs_path))

    paths = tuple(map(to_path, db.fs.get_paths(*obj_ids, session=session)))
    results = results_.CachingResults(iter(paths), representer=str)

    if len(obj_or_ids) == 1 and len(results) == 1:
        return results[0]

    return results


def _get_obj_ids(entries, session: "pyos.Session") -> tuple:
    """Get the object ids from objects, ids, paths or filesystem nodes (e.g. the results of find)"""
    obj_ids, rest = psh_lib.gather_obj_ids(entries, session.historian)
    for entry in rest:
        node = _to_node(entry, session)
        if isinstance(node, fs.ObjectNode):
            obj_ids.append(node.obj_id)
        elif isinstance(node, fs.ContainerNode):
            obj_ids.extend(child.obj_id for child in node.objects)
        else:
            raise ValueError(f"Cannot locate '{entry}'")

    return tuple(obj_ids)


def _to_node(entry, session: "pyos.Session") -> "fs.BaseNode":
    if isinstance(entry, fs.BaseNode):
        return entry
    if isinstance(entry, str):
        entry = pathlib.PurePath(entry)
    return fs.to_node(entry, session=session)


class Locate(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument("obj_ids", nargs="*", type=str)

    @cmd2.with_argparser(parser)
    def do_locate(self, args):
        print(locate(*args.obj_ids))
