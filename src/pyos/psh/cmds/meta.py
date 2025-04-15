"""The meta command"""

import argparse
import logging
import sys

import cmd2

from . import ls
from .. import completion, flags
from ... import _globals, db, fs, psh_lib
from ... import results as results_

logger = logging.getLogger(__name__)


@psh_lib.command(pass_options=True)
@psh_lib.flag(flags.s, "Set the metadata")
@psh_lib.flag(flags.u, "Update the metadata")
def meta(options, *obj_or_ids, **updates):  # pylint: disable=too-many-return-statements
    """Get, set or update the metadata on one or more objects"""
    # pylint: disable=too-many-branches
    if not obj_or_ids:
        return None

    hist = _globals.get_global_session().historian
    obj_ids, rest = psh_lib.gather_obj_ids(obj_or_ids, hist)

    # Assume that anything left is something like a path or filesystem node
    if rest:
        to_update = ls(-flags.d, *rest)
        for node in to_update:
            if isinstance(node, fs.ObjectNode):
                obj_ids.append(node.obj_id)
            else:
                print(f"Can't set metadata on '{node}'")

    if options.pop(flags.u, False):
        # In 'update' mode
        if updates:
            db.lib.update_meta(*obj_ids, meta=updates)

    elif options.pop(flags.s, False):
        # In 'setting' mode
        if updates:
            db.lib.set_meta(*obj_ids, meta=updates)

    else:
        # In 'getting' mode
        if updates:
            logging.warning("Keywords supplied to meta without -s/-u flags: %s", updates)

        if len(obj_ids) == 1:
            # Special case for a single parameter
            metadata = db.lib.get_meta(obj_ids[0])
            if metadata is None:
                return None
            return results_.ResultsDict(metadata)

        return results_.CachingResults(db.lib.find_meta(obj_ids=obj_ids))

    return None


class Meta(cmd2.CommandSet):
    parser = argparse.ArgumentParser()

    set_update = parser.add_mutually_exclusive_group()
    set_update.add_argument("-s", action="store_true", help="set the metadata")
    set_update.add_argument("-u", action="store_true", help="update the metadata")
    parser.add_argument("path", nargs="*", type=str, completer_method=completion.path_complete)

    @cmd2.with_argparser(parser)
    def do_meta(self, args):
        command = meta
        if args.u:
            command = command - flags.u
        if args.s:
            command = command - flags.s

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
