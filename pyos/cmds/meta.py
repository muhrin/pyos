"""The meta command"""

import logging

import pyos
from .ls import ls
from . import flags

logger = logging.getLogger(__name__)


@pyos.opts.flag(flags.s, "Set the metadata")
@pyos.opts.flag(flags.u, "Update the metadata")
def meta(*obj_or_ids, **updates):
    """Get, set or update the metadata on one or more objects"""
    options, rest = pyos.opts.separate_opts(*obj_or_ids)
    if not rest:
        return None

    to_update = ls(flags.d, *rest)
    obj_ids = []
    for node in to_update:
        if isinstance(node, pyos.ObjectNode):
            obj_ids.append(node.obj_id)
        else:
            print("Can't set metadata on '{}'".format(node))

    if options.pop(flags.u, False):
        # In 'update' mode
        if not updates:
            return None
        pyos.lib.update_meta(*obj_ids, meta=updates)
    elif options.pop(flags.s, False):
        # In 'setting' mode
        if not updates:
            return None
        pyos.lib.set_meta(*obj_ids, meta=updates)
    else:
        # In 'getting' mode
        if updates:
            logging.warning("Keywords supplied to meta without -s/-u flags: %s", updates)

        if len(obj_ids) == 1:
            # Special case for a single parameter
            return pyos.ResultsDict(next(pyos.lib.get_meta(*obj_ids)))

        return pyos.CachingResults(pyos.lib.get_meta(*obj_ids))

    return None
