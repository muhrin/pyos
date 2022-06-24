# -*- coding: utf-8 -*-
"""The locate command"""
import argparse
from typing import Optional, Union, Sequence

import cmd2

import pyos
from pyos import db


@pyos.psh_lib.command()
def locate(*obj_or_ids) -> Optional[Union[pyos.pathlib.Path, Sequence[pyos.pathlib.Path]]]:
    """Locate the directory of one or more objects"""
    if not obj_or_ids:
        return None

    hist = db.get_historian()
    obj_ids = tuple(map(hist.to_obj_id, obj_or_ids))

    # Convert to abspaths
    def to_path(fs_path):
        return pyos.pathlib.Path(pyos.os.withdb.from_fs_path(fs_path))

    paths = tuple(map(to_path, db.fs.get_paths(*obj_ids, historian=hist)))
    results = pyos.psh_lib.CachingResults(iter(paths), representer=str)

    if len(obj_or_ids) == 1 and len(results) == 1:
        return results[0]

    return results


class Locate(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument('obj_ids', nargs='*', type=str)

    @cmd2.with_argparser(parser)
    def do_locate(self, args):
        print(locate(*args.obj_ids))
