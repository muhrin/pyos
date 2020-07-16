"""Print working directory command"""
import argparse

import cmd2

import pyos


@pyos.psh_lib.command()
def pwd() -> pyos.pathlib.Path:
    """Return the current working directory"""
    return pyos.pathlib.Path().resolve()


parser = argparse.ArgumentParser()  # pylint: disable=invalid-name


@cmd2.with_argparser(parser)
def do_pwd(self, _):
    self.poutput(pwd())
