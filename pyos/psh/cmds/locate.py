"""The locate command"""
import argparse
from typing import Optional, Union, Sequence

import cmd2

import pyos
from pyos import psh


@pyos.psh_lib.command()
def locate(*obj_or_ids) -> Optional[Union[pyos.pathlib.Path, Sequence[pyos.pathlib.Path]]]:
    """Locate the directory of one or more objects"""
    if not obj_or_ids:
        return None

    to_locate = psh.ls(-psh.d, *obj_or_ids)
    # Convert to abspaths
    paths = [node.abspath for node in to_locate]
    results = pyos.psh_lib.CachingResults(paths.__iter__(), representer=str)

    if len(obj_or_ids) == 1 and len(results) == 1:
        return results[0]

    return results


class Locate(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument('obj_ids', nargs='*', type=str)

    @cmd2.with_argparser(parser)
    def do_locate(self, args):  # pylint: disable=no-self-use
        print(locate(*args.obj_ids))
