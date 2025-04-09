"""The tree command"""

import argparse

import cmd2

from . import ls
from .. import completion, flags
from ... import fs, psh_lib


@psh_lib.command(pass_options=True)
@psh_lib.option(flags.L, help="max display depth of the directory tree")
def tree(options, *paths):
    """Get a tree representation of the given paths"""
    to_tree = ls(-flags.d, *paths)
    level = options.pop(flags.L, -1)
    # Fully expand all directories
    for dir_node in to_tree.directories:
        dir_node.expand(level)
    to_tree.show(mode=fs.TREE_VIEW)
    return to_tree


class Tree(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument("-L", type=int, help="max display depth of the directory tree")
    parser.add_argument("path", nargs="*", type=str, completer_method=completion.path_complete)

    @cmd2.with_argparser(parser)
    def do_tree(self, args):
        command = tree
        if args.L is not None:
            command = command - flags.L(args.L)

        print(command(*args.path))
