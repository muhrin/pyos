"""The meta command"""
import argparse
import logging
import sys

import cmd2

import pyos
from pyos.psh import completion
from pyos import psh

logger = logging.getLogger(__name__)


@pyos.psh_lib.command(pass_options=True)
@pyos.psh_lib.flag(psh.s, "Set the metadata")
@pyos.psh_lib.flag(psh.u, "Update the metadata")
def meta(options, *obj_or_ids, **updates):
    """Get, set or update the metadata on one or more objects"""
    if not obj_or_ids:
        return None

    to_update = psh.ls(-psh.d, *obj_or_ids)
    obj_ids = []
    for node in to_update:
        if isinstance(node, pyos.fs.ObjectNode):
            obj_ids.append(node.obj_id)
        else:
            print("Can't set metadata on '{}'".format(node))

    if options.pop(psh.u, False):
        # In 'update' mode
        if not updates:
            return None
        pyos.db.lib.update_meta(*obj_ids, meta=updates)
    elif options.pop(psh.s, False):
        # In 'setting' mode
        if not updates:
            return None
        pyos.db.lib.set_meta(*obj_ids, meta=updates)
    else:
        # In 'getting' mode
        if updates:
            logging.warning("Keywords supplied to meta without -s/-u flags: %s", updates)

        if len(obj_ids) == 1:
            # Special case for a single parameter
            return pyos.psh_lib.ResultsDict(pyos.db.lib.get_meta(obj_ids[0]))

        return pyos.psh_lib.CachingResults(pyos.db.lib.find_meta(obj_ids=obj_ids))

    return None


class Meta(cmd2.CommandSet):
    parser = argparse.ArgumentParser()

    set_update = parser.add_mutually_exclusive_group()
    set_update.add_argument('-s', action='store_true', help="set the metadata")
    set_update.add_argument('-u', action='store_true', help="update the metadata")
    parser.add_argument('path', nargs='*', type=str, completer_method=completion.path_complete)

    @cmd2.with_argparser(parser)
    def do_meta(self, args):  # pylint: disable=no-self-use
        command = meta
        if args.u:
            command = command - psh.u
        if args.s:
            command = command - psh.s

        if not args.path:
            # Read from standard in
            try:
                args.path = [line.rstrip() for line in sys.stdin.readlines()]
            except Exception:
                logger.exception("Exception trying to readlines")
                raise

        logger.debug("Writing to %s", sys.stdout)
        result = command(*args.path)
        rep = repr(result)
        print(rep, file=sys.stdout)
