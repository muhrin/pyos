"""Print working directory command"""

import argparse

import cmd2

from .. import completion, flags
from ... import os, psh_lib


@psh_lib.command(pass_options=True)
@psh_lib.flag(flags.p, "no error if existing, make parent directories as needed")
def mkdir(options, directory: os.PathSpec):
    """make directories"""
    if options.pop(flags.p):
        os.makedirs(directory, exists_ok=True)
    else:
        os.makedirs(directory)


class Mkdir(cmd2.CommandSet):
    __doc__ = mkdir.__doc__

    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs=1, type=str, completer_method=completion.dir_completer)
    parser.add_argument(
        "-p",
        action="store_true",
        help="no error if existing, make parent directories as needed",
    )

    @cmd2.with_argparser(parser)
    def do_mkdir(self, args):
        new_dir = args.path[0]

        command = mkdir
        if args.p:
            command = command - flags.p

        res = command(new_dir)
        if res is not None:
            print(res)
