import os
import sys

import click
import mincepy
import mincepy.archive_factory

from pyos import _globals, psh

URI_HELP = (
    "the URI of the archive to connect to, e.g. litemongo:///path/to/dir#db or "
    "litemongo://?engine=memory#db (in memory).  Defaults to $MINCEPY_ARCHIVE, if set, "
    "otherwise use 'connect' from within the shell"
)


def _connect(uri: str):
    """Connect to the given archive or, if there isn't one, the default from the environment (if
    set).  Without either, the shell starts unconnected rather than waiting for a server that may
    not be there"""
    uri = uri or os.environ.get(mincepy.archive_factory.ENV_ARCHIVE_URI, "")
    if not uri:
        return

    try:
        _globals.connect(uri)
    except mincepy.ConnectionError as exc:
        raise click.ClickException(f"Failed to connect to '{uri}': {exc}") from exc


@click.command(name="psh")
@click.argument("script", default="")
@click.option("-c", "--cmd", required=False, help="commands to be invoked directly")
@click.option("--uri", default="", help=URI_HELP)
def psh_(script, cmd, uri):
    _connect(uri)

    headless_cmds = None
    if cmd:
        headless_cmds = list(part.strip() for part in cmd.split(";"))
    elif script:
        with open(script, "r", encoding="utf-8") as script_file:
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
@click.option("--uri", default="", help=URI_HELP)
def shell(uri):
    """Start the pyos shell"""
    _connect(uri)
    # Need to clear args because otherwise cmd2 picks them up
    app = psh.PyosShell()
    sys.exit(app.cmdloop())
