"""The save command"""

import pyos
from pyos import psh


@pyos.psh_lib.command(pass_options=True)
@pyos.psh_lib.flag(psh.f, help="Force - overwrite files with the same name")
def save(options, *args):
    """Save one or more objects"""
    objs = args

    if len(objs) > 1 and isinstance(objs[-1], (str, pyos.pathlib.PurePath)):
        # Extract the destination
        dest = pyos.pathlib.Path(objs[-1]).resolve()
        objs = objs[:-1]

        if len(objs) > 1 and dest.is_file():
            # Automatically convert to directory if there are many objects as they can't save
            # more than one with the same filename in the same folder!
            dest = dest.to_dir()

        save_args = [(obj, dest) for obj in objs]
    else:
        save_args = [(obj, None) for obj in objs]

    saved = pyos.db.save_many(save_args, overwrite=psh.f in options)

    if len(objs) == 1:
        return saved[0]

    return saved
