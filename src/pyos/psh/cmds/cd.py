"""Change directory command"""

import argparse

import cmd2

from .. import completion
from ... import exceptions, os, psh_lib


@psh_lib.command()
def cd(path: os.PathSpec):  # pylint: disable=invalid-name
    """Change the current working directory"""
    path = os.path.normpath(os.path.expanduser(path))
    try:
        os.chdir(path)
    except exceptions.PyOSError as exc:
        print(exc)


class Cd(cmd2.CommandSet):

    def __init__(self):
        super().__init__()
        self._prev_dir = "~"

    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs=1, type=str, completer_method=completion.dir_completer)

    @cmd2.with_argparser(parser)
    def do_cd(self, args):
        current_dir = os.getcwd()
        new_dir = args.path[0] if args.path[0] != "-" else self._prev_dir
        cd(new_dir)
        self._prev_dir = current_dir
