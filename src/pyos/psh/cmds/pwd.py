"""Print working directory command"""

import argparse

import cmd2

from ... import pathlib, psh_lib


@psh_lib.command()
def pwd() -> pathlib.Path:
    """Return the current working directory"""
    return pathlib.Path().resolve()


class Pwd(cmd2.CommandSet):
    parser = argparse.ArgumentParser()

    @cmd2.with_argparser(parser)
    def do_pwd(self, _):
        print(pwd())
