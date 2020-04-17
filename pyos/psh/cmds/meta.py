"""The meta command"""

import logging

import pyos
from pyos import psh

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


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
