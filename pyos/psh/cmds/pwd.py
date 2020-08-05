"""Print working directory command"""
import argparse

import cmd2

import pyos


@pyos.psh_lib.command()
def pwd() -> pyos.pathlib.Path:
    """Return the current working directory"""
    return pyos.pathlib.Path().resolve()


class Pwd(cmd2.CommandSet):
    parser = argparse.ArgumentParser()

    @cmd2.with_argparser(parser)
    def do_pwd(self, app, _):  # pylint: disable=no-self-use
        app.poutput(pwd())
