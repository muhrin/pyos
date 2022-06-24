# -*- coding: utf-8 -*-
"""The remove command"""
import argparse
import copy

import cmd2
import tqdm

import pyos
from pyos import psh
from pyos.psh import completion


def _remove_directories(nodes):
    filtered = pyos.fs.ResultsNode()
    for node in nodes:
        if isinstance(node, pyos.fs.DirectoryNode):
            print(f"rm: cannot remove '{node.abspath.name}': Is a directory")
        elif isinstance(node, pyos.fs.ResultsNode):
            filtered.extend(_remove_directories(node))
        else:
            filtered.append(copy.copy(node))
    return filtered


@pyos.psh_lib.command(pass_options=True)
@pyos.psh_lib.flag(psh.p, help='show progress bar')
@pyos.psh_lib.flag(psh.r, help='remove directories and their contents recursively')
def rm(options, *obj_or_ids):  # pylint: disable=invalid-name
    """Remove objects"""
    if not obj_or_ids:
        return

    hist = pyos.db.get_historian()
    obj_ids, rest = pyos.psh_lib.gather_obj_ids(obj_or_ids, hist)

    with hist.transaction():
        for obj_id in obj_ids:
            hist.delete(obj_id)

    # Assume that anything left is something like a path or filesystem node
    to_delete = psh.ls(-psh.d, *rest)
    recursive = options.pop(psh.flags.r)
    if not recursive:
        to_delete = _remove_directories(to_delete)

    if to_delete:
        if options.pop(psh.flags.p):
            to_delete = tqdm.tqdm(to_delete, desc='rm')

        for node in to_delete:
            node.delete()


class Rm(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', action='store_true', help='show progress bar')
    parser.add_argument('-r',
                        action='store_true',
                        help='remove directories and their contents recursively')
    parser.add_argument('path', nargs='*', type=str, completer_method=completion.path_complete)

    @cmd2.with_argparser(parser)
    def do_rm(self, args):
        command = rm
        if args.r:
            command = command - psh.r
        if args.p:
            command = command - psh.p

        res = command(*args.path)
        if res is not None:
            print(res)
