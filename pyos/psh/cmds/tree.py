"""The tree command"""
import argparse

import cmd2

import pyos
from pyos import psh
from pyos.psh import base


@pyos.psh_lib.command(pass_options=True)
@pyos.psh_lib.option(psh.flags.L, help='max display depth of the directory tree')
def tree(options, *paths):
    """Get a tree representation of the given paths"""
    to_tree = psh.ls(-psh.d, *paths)
    level = options.pop(psh.L, -1)
    # Fully expand all directories
    for dir_node in to_tree.directories:
        dir_node.expand(level)
    to_tree.show(mode=pyos.fs.TREE_VIEW)
    return to_tree


class Tree(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument('-L', type=int, help="max display depth of the directory tree")
    parser.add_argument('path', nargs='*', type=str, completer_method=base.path_complete)

    @cmd2.with_argparser(parser)
    def do_tree(self, app: cmd2.Cmd, args):  # pylint: disable=no-self-use
        command = tree
        if args.L is not None:
            command = command - psh.L(args.L)

        app.poutput(command(*args.path))
