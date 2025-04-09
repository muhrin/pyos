"""List command"""

import argparse
import logging

import cmd2

from .. import completion, flags
from ... import fs, pathlib, psh_lib

logger = logging.getLogger(__name__)


@psh_lib.command(pass_options=True)
@psh_lib.flag(flags.l, help="use a long listing format")
@psh_lib.flag(flags.d, help="list directories themselves, not their contents")
@psh_lib.flag(flags.p, help="print the str() value of each object")
@psh_lib.flag(
    psh_lib.Option(1),
    help="list one file per line.  This will avoid waiting for all results to be loaded before printing",
)
def ls(options, *args) -> fs.ContainerNode:  # pylint: disable=invalid-name, too-many-branches
    """List the contents of a directory

    :type: restrict listing to a particular type
    """
    rest = args
    parsed = psh_lib.parse_fs_entry(*rest)

    results = fs.ResultsNode()
    if rest:
        for entry in parsed:
            if isinstance(entry, Exception):
                raise entry

            try:
                results.append(fs.to_node(entry))
            except ValueError as exc:
                logger.info(str(exc))
    else:
        results.append(fs.to_node(pathlib.Path()))

    if not options.pop(flags.d):
        for entry in results:
            if isinstance(entry, fs.DirectoryNode):
                entry.expand(populate_objects=flags.l in options)

        if len(results) == 1 and isinstance(results[0], fs.DirectoryNode):
            # We just have a single directory
            results = results[0]

    if options.pop(flags.l):
        properties = ["loaded", "type", "version", "mtime", "name"]
        if options.pop(flags.p):
            properties.append("str")
        results.show(*properties, mode=fs.TABLE_VIEW)
    elif options.pop(1):
        results.show(mode=fs.SINGLE_COLUMN_VIEW)
    else:
        results.show(mode=fs.LIST_VIEW)

    return results


class Ls(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", action="store_true", help="use a long listing format")
    parser.add_argument(
        "-d",
        action="store_true",
        help="list directories themselves, not their contents",
    )
    parser.add_argument("-p", action="store_true", help="print the str() value of each object")
    parser.add_argument(
        "-1",
        action="store_true",
        help="list one file per line.  This will avoid waiting for all results to be loaded before "
        "printing",
    )
    parser.add_argument("path", nargs="*", type=str, completer_method=completion.path_complete)

    @cmd2.with_argparser(parser)
    def do_ls(self, args):
        command = ls
        if args.l:
            command = command - flags.l
        if args.d:
            command = command - flags.d
        if args.p:
            command = command - flags.p
        if vars(args)["1"]:
            command = command - psh_lib.Option(1)

        res = command(*args.path)
        res.__stream_out__(self._cmd.stdout)
