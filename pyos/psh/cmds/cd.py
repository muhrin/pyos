"""Change directory command"""
import argparse
import functools

import cmd2

import pyos
from pyos.psh import base


@pyos.psh_lib.command()
def cd(path: pyos.os.PathSpec):  # pylint: disable=invalid-name
    """Change the current working directory"""
    path = pyos.pathlib.PurePath(path)
    if path.is_file_path():
        # Assume they just left out the slash
        path = path.to_dir()

    pyos.os.chdir(path)


class Cd(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument('path',
                        nargs=1,
                        type=str,
                        completer_method=functools.partial(base.dir_completer))

    @cmd2.with_argparser(parser)
    def do_cd(self, _app: cmd2.Cmd, args):  # pylint: disable=no-self-use
        cd(args.path[0])
