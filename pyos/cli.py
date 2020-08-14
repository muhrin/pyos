import sys

import click

from pyos import psh


@click.command(name='psh')
@click.argument('script', default='')
@click.option('-c', '--cmd', required=False, help="commands to be invoked directly")
def psh_(script, cmd):
    headless_cmds = None
    if cmd:
        headless_cmds = list(part.strip() for part in cmd.split(';'))
    elif script:
        with open(script, 'r') as script_file:
            headless_cmds = list(line.rstrip() for line in script_file.readlines())

    # Need to clear args because otherwise cmd2 picks them up
    if headless_cmds:
        psh.PyosShell.execute(*headless_cmds)
        return

    app = psh.PyosShell()
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
