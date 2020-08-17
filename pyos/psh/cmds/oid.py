"""The object id command"""
import argparse
import logging
import sys

import cmd2

import pyos
from pyos import db
from pyos.psh_lib import CachingResults

_LOGGER = logging.getLogger(__name__)


@pyos.psh_lib.command()
def oid(*args):
    """Get the object id for one or more live objects"""
    if not args:
        return None

    result = CachingResults(db.get_oid(*args), representer=str)

    if len(result) == 1:
        return result[0]

    return result


class Oid(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument('objs', nargs='*', type=str, help='the objects to get ids for')

    @cmd2.with_argparser(parser)
    def do_oid(self, args):  # pylint: disable=no-self-use
        if not args.objs:
            # Read from standard in
            _LOGGER.debug("oid: getting input from stdin")
            try:
                args.path = [line.rstrip() for line in sys.stdin.readlines()]
            except Exception:
                _LOGGER.exception("Exception trying to readlines")
                raise
            _LOGGER.debug("oid: got input' %s' from stdin", args.path)

        print(oid(*args.path))
