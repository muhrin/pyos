import sys

import click

from pyos import psh


@click.command(name='psh')
@click.argument('script', default='')
def psh_(script):
    # Need to clear args because otherwise cmd2 picks them up
    app = psh.PyosShell(startup_script=script)
    sys.exit(app.cmdloop())


@click.group()
def pyos():
    pass


@pyos.command()
def shell():
    """Start the pyos shell"""
    # Need to clear args because otherwise cmd2 picks them up
    app = psh.PyosShell()
    sys.exit(app.cmdloop())
