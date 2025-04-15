"""The locate command"""

import argparse
from typing import Optional, Sequence, Union

import cmd2

from ... import _globals, db, os, pathlib, psh_lib
from ... import results as results_


@psh_lib.command()
def locate(
    *obj_or_ids,
) -> Optional[Union[pathlib.Path, Sequence[pathlib.Path]]]:
    """Locate the directory of one or more objects"""
    if not obj_or_ids:
        return None

    session = _globals.get_global_session()
    obj_ids = tuple(map(session.historian.to_obj_id, obj_or_ids))

    # Convert to abspaths
    def to_path(fs_path):
        return pathlib.Path(os.withdb.from_fs_path(fs_path))

    paths = tuple(map(to_path, db.fs.get_paths(*obj_ids, session=session)))
    results = results_.CachingResults(iter(paths), representer=str)

    if len(obj_or_ids) == 1 and len(results) == 1:
        return results[0]

    return results


class Locate(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument("obj_ids", nargs="*", type=str)

    @cmd2.with_argparser(parser)
    def do_locate(self, args):
        print(locate(*args.obj_ids))
