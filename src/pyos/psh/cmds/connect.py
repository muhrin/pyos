"""The connection commands"""

import argparse
import sys
from typing import TYPE_CHECKING

import cmd2
import mincepy

from ... import _globals

if TYPE_CHECKING:
    import pyos


class Connnection(cmd2.CommandSet):
    connect_parser = argparse.ArgumentParser()
    connect_parser.add_argument("uri", type=str, help="the URI of the archive to connect to")

    @cmd2.with_argparser(connect_parser)
    def do_connect(self, args):
        """Connect to a mincepy archive"""
        app = self._cmd
        if app.in_script() and getattr(app, "uri", ""):
            print(
                f"Skipping 'connect {args.uri}' from the script, using '{app.uri}' given on the "
                "command line",
                file=sys.stderr,
            )
            return

        try:
            _globals.connect(args.uri)
            print(f"Connected to {args.uri}")
        except mincepy.ConnectionError as exc:
            print(f"Error: {exc}", file=sys.stderr)

    def do_disconnect(self, _args):
        """Disconnect from the current archive"""
        if _globals.get_global_session() is None:
            print("Not connected", file=sys.stderr)
            return

        _globals.reset_global_session()
