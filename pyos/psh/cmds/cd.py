"""Change directory command"""
import argparse

import cmd2

import pyos
from pyos.psh import completion


@pyos.psh_lib.command()
def cd(path: pyos.os.PathSpec):  # pylint: disable=invalid-name
    """Change the current working directory"""
    path = pyos.os.path.normpath(pyos.os.path.expanduser(path))
    path = pyos.pathlib.PurePath(path)
    if path.is_file_path():
        # Assume they just left out the slash
        path = path.to_dir()

    pyos.os.chdir(path)


class Cd(cmd2.CommandSet):

    def __init__(self):
        super().__init__()
        self._prev_dir = '~'

    parser = argparse.ArgumentParser()
    parser.add_argument('path', nargs=1, type=str, completer_method=completion.dir_completer)

    @cmd2.with_argparser(parser)
    def do_cd(self, args):
        current_dir = pyos.os.getcwd()
        new_dir = args.path[0] if args.path[0] != '-' else self._prev_dir
        cd(new_dir)
        self._prev_dir = current_dir
