"""The save command"""

import pyos
from .. import opts
from . import flags


@opts.flag(flags.f, help="Force - overwrite files with the same name")
def save(*args):
    """Save one or more objects"""
    options = args[0]
    objs = args[1:]

    if len(objs) > 1 and isinstance(objs[-1], (str, pyos.PyosPath)):
        # Extract the destination
        dest = pyos.PyosPath(objs[-1]).resolve()
        objs = objs[:-1]

        if len(objs) > 1 and dest.is_file():
            # Automatically convert to directory if there are many objects as they can't save
            # more than one with the same filename in the same folder!
            dest = dest.to_dir()

        save_args = tuple((obj, dest) for obj in objs)
        saved = pyos.lib.save_many(save_args, overwrite=flags.f in options)
    else:
        saved = pyos.lib.save_many(objs, overwrite=flags.f in options)

    if len(objs) == 1:
        return saved[0]

    return saved