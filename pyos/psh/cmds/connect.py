"""The connection commands"""
import argparse

import cmd2
import mincepy

from pyos import db


class Connnection(cmd2.CommandSet):
    connect_parser = argparse.ArgumentParser()
    connect_parser.add_argument('uri', type=str, help='the URI of the archive to connect to')

    @cmd2.with_argparser(connect_parser)
    def do_connect(self, app: cmd2.Cmd, args):  # pylint: disable=no-self-use
        """Connect to a mincepy archive"""
        try:
            db.connect(args.uri)
            app.poutput("Connected to {}".format(args.uri))
        except mincepy.ConnectionError as exc:
            app.perror("Error: {}".format(exc))

    def do_disconnect(self, _app: cmd2.Cmd, _cmd):  # pylint: disable=no-self-use
        """Disconnect from the current archive"""
        db.reset()
