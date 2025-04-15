"""The connection commands"""

import argparse
import sys
from typing import TYPE_CHECKING, Optional

import cmd2
import mincepy

from ... import _globals

if TYPE_CHECKING:
    import pyos


class Connnection(cmd2.CommandSet):

    connect_parser = argparse.ArgumentParser()
    connect_parser.add_argument("uri", type=str, help="the URI of the archive to connect to")
    _session: Optional["pyos.Session"] = None

    @cmd2.with_argparser(connect_parser)
    def do_connect(self, args):
        """Connect to a mincepy archive"""
        try:
            self._session = _globals.connect(args.uri)
            print(f"Connected to {args.uri}")
        except mincepy.ConnectionError as exc:
            print(f"Error: {exc}", file=sys.stderr)

    def do_disconnect(self, _args):
        """Disconnect from the current archive"""
        self._session.close()
        self._session = None
