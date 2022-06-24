# -*- coding: utf-8 -*-
"""List command"""
import argparse
import logging

import cmd2

import pyos
from pyos import psh
from pyos import psh_lib
from pyos.psh import completion

logger = logging.getLogger(__name__)


@psh_lib.command(pass_options=True)
@psh_lib.flag(psh.l, help='use a long listing format')
@psh_lib.flag(psh.d, help='list directories themselves, not their contents')
@psh_lib.flag(psh.p, help='print the str() value of each object')
@psh_lib.flag(
    psh_lib.Option(1),
    help=
    'list one file per line.  This will avoid waiting for all results to be loaded before printing')
def ls(options, *args) -> pyos.fs.ContainerNode:  # pylint: disable=invalid-name, too-many-branches
    """List the contents of a directory

    :type: restrict listing to a particular type
    """
    rest = args
    parsed = pyos.psh_lib.parse_fs_entry(*rest)

    results = pyos.fs.ResultsNode()
    if rest:
        for entry in parsed:
            if isinstance(entry, Exception):
                raise entry

            try:
                results.append(pyos.fs.to_node(entry))
            except ValueError as exc:
                logger.info(str(exc))
    else:
        results.append(pyos.fs.to_node(pyos.pathlib.Path()))

    if not options.pop(psh.d):
        for entry in results:
            if isinstance(entry, pyos.fs.DirectoryNode):
                entry.expand(populate_objects=psh.l in options)

        if len(results) == 1 and isinstance(results[0], pyos.fs.DirectoryNode):
            # We just have a single directory
            results = results[0]

    if options.pop(psh.l):
        properties = ['loaded', 'type', 'version', 'mtime', 'name']
        if options.pop(psh.p):
            properties.append('str')
        results.show(*properties, mode=pyos.fs.TABLE_VIEW)
    elif options.pop(1):
        results.show(mode=pyos.fs.SINGLE_COLUMN_VIEW)
    else:
        results.show(mode=pyos.fs.LIST_VIEW)

    return results


class Ls(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', action='store_true', help='use a long listing format')
    parser.add_argument('-d',
                        action='store_true',
                        help='list directories themselves, not their contents')
    parser.add_argument('-p', action='store_true', help='print the str() value of each object')
    parser.add_argument(
        '-1',
        action='store_true',
        help='list one file per line.  This will avoid waiting for all results to be loaded before '
        'printing')
    parser.add_argument('path', nargs='*', type=str, completer_method=completion.path_complete)

    @cmd2.with_argparser(parser)
    def do_ls(self, args):
        command = ls
        if args.l:
            command = command - psh.l
        if args.d:
            command = command - psh.d
        if args.p:
            command = command - psh.p
        if vars(args)['1']:
            command = command - psh_lib.Option(1)

        res = command(*args.path)
        res.__stream_out__(self._cmd.stdout)
