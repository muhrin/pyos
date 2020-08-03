import sys

import click

from pyos import psh


@click.group()
def pyos():
    pass


@pyos.command()
# @click.argument('cmd', type=str)
def shell():
    """Start the pyos shell"""
    # Need to clear args because otherwise cmd2 picks them up
    sys.argv = [sys.argv[0]]
    app = psh.PyosShell()
    sys.exit(app.cmdloop())
