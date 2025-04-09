"""The object id command"""

import argparse
import logging
import sys

import cmd2

from .. import completion
from ... import db, psh_lib
from ... import results as results_

_LOGGER = logging.getLogger(__name__)


@psh_lib.command()
def oid(*args):
    """Get the object id for one or more live objects"""
    if not args:
        return None

    result = results_.CachingResults(db.get_oid(*args), representer=str)

    if len(result) == 1:
        return result[0]

    return result


class Oid(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    # parser.add_argument('objs', nargs='*', type=str, help='the objects to get ids for')
    parser.add_argument(
        "path",
        nargs="*",
        type=str,
        completer_method=completion.path_complete,
        help="the objects to get ids for",
    )

    @cmd2.with_argparser(parser)
    def do_oid(self, args):
        if not args.path:
            # Read from standard in
            _LOGGER.debug("oid: getting input from stdin")
            try:
                args.path = [line.rstrip() for line in sys.stdin.readlines()]
            except Exception:
                _LOGGER.exception("Exception trying to readlines")
                raise
            _LOGGER.debug("oid: got input' %s' from stdin", args.path)

        print(oid(*args.path))
