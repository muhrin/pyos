"""The object id command"""

import mincepy

import pyos


@pyos.psh_lib.command()
def oid(*args):
    """Get the object id for one or more live objects"""
    if not args:
        return None

    hist = mincepy.get_historian()

    oids = []
    for obj in args:
        try:
            oids.append(hist.get_obj_id(obj))
        except mincepy.NotFound:
            oids.append(None)

    if len(oids) == 1:
        return oids[0]

    return oids
