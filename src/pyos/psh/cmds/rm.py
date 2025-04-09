"""The remove command"""

import argparse
import copy

import cmd2
import tqdm

from . import ls
from .. import completion, flags
from ... import db, fs, psh_lib


def _remove_directories(nodes):
    filtered = fs.ResultsNode()
    for node in nodes:
        if isinstance(node, fs.DirectoryNode):
            print(f"rm: cannot remove '{node.abspath.name}': Is a directory")
        elif isinstance(node, fs.ResultsNode):
            filtered.extend(_remove_directories(node))
        else:
            filtered.append(copy.copy(node))
    return filtered


@psh_lib.command(pass_options=True)
@psh_lib.flag(flags.p, help="show progress bar")
@psh_lib.flag(flags.r, help="remove directories and their contents recursively")
def rm(options, *obj_or_ids):  # pylint: disable=invalid-name
    """Remove objects"""
    if not obj_or_ids:
        return

    hist = db.get_historian()
    obj_ids, rest = psh_lib.gather_obj_ids(obj_or_ids, hist)

    with hist.transaction():
        for obj_id in obj_ids:
            hist.delete(obj_id)

    # Assume that anything left is something like a path or filesystem node
    to_delete = ls(-flags.d, *rest)
    recursive = options.pop(flags.r)
    if not recursive:
        to_delete = _remove_directories(to_delete)

    if to_delete:
        if options.pop(flags.p):
            to_delete = tqdm.tqdm(to_delete, desc="rm")

        for node in to_delete:
            node.delete()


class Rm(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", action="store_true", help="show progress bar")
    parser.add_argument(
        "-r",
        action="store_true",
        help="remove directories and their contents recursively",
    )
    parser.add_argument("path", nargs="*", type=str, completer_method=completion.path_complete)

    @cmd2.with_argparser(parser)
    def do_rm(self, args):
        command = rm
        if args.r:
            command = command - flags.r
        if args.p:
            command = command - flags.p

        res = command(*args.path)
        if res is not None:
            print(res)
