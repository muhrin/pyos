"""The object id command"""

import mincepy

from pyos import psh_lib


def oid(*args):
    """Get the object id for one or more live objects"""
    _options, rest = psh_lib.opts.separate_opts(*args)
    if not rest:
        return None

    hist = mincepy.get_historian()

    oids = []
    for obj in rest:
        try:
            oids.append(hist.get_obj_id(obj))
        except mincepy.NotFound:
            oids.append(None)

    if len(oids) == 1:
        return oids[0]

    return oids
