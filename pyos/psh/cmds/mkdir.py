# -*- coding: utf-8 -*-
"""Print working directory command"""
import argparse

import cmd2

import pyos
from pyos import psh


@pyos.psh_lib.command(pass_options=True)
@pyos.psh_lib.flag(psh.p, 'no error if existing, make parent directories as needed')
def mkdir(options, directory: pyos.os.PathSpec):
    """make directories"""
    if options.pop(psh.p):
        pyos.os.makedirs(directory, exists_ok=True)
    else:
        pyos.os.makedirs(directory)


class Mkdir(cmd2.CommandSet):
    __doc__ = mkdir.__doc__

    parser = argparse.ArgumentParser()
    parser.add_argument('path', nargs=1, type=str, completer_method=psh.completion.dir_completer)
    parser.add_argument('-p',
                        action='store_true',
                        help='no error if existing, make parent directories as needed')

    @cmd2.with_argparser(parser)
    def do_mkdir(self, args):
        new_dir = args.path[0]

        command = mkdir
        if args.p:
            command = command - psh.p

        res = command(new_dir)
        if res is not None:
            print(res)
