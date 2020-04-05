"""The meta command"""

import logging

import pyos
from pyos import pysh

logger = logging.getLogger(__name__)


@pyos.shell.flag(pysh.s, "Set the metadata")
@pyos.shell.flag(pysh.u, "Update the metadata")
def meta(*obj_or_ids, **updates):
    """Get, set or update the metadata on one or more objects"""
    options, rest = pyos.shell.separate_opts(*obj_or_ids)
    if not rest:
        return None

    to_update = pysh.ls(-pysh.d, *rest)
    obj_ids = []
    for node in to_update:
        if isinstance(node, pyos.fs.ObjectNode):
            obj_ids.append(node.obj_id)
        else:
            print("Can't set metadata on '{}'".format(node))

    if options.pop(pysh.u, False):
        # In 'update' mode
        if not updates:
            return None
        pyos.db.lib.update_meta(*obj_ids, meta=updates)
    elif options.pop(pysh.s, False):
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
            return pyos.shell.ResultsDict(next(pyos.db.lib.get_meta(*obj_ids)))

        return pyos.shell.CachingResults(pyos.db.lib.get_meta(*obj_ids))

    return None
