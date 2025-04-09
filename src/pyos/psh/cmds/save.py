"""The save command"""

from .. import flags
from ... import db, pathlib, psh_lib


@psh_lib.command(pass_options=True)
@psh_lib.flag(flags.f, help="Force - overwrite files with the same name")
def save(options, *args):
    """Save one or more objects"""
    objs = args

    if len(objs) > 1 and isinstance(objs[-1], (str, pathlib.PurePath)):
        # Extract the destination
        dest = pathlib.Path(objs[-1]).resolve()
        objs = objs[:-1]

        save_args = [(obj, dest) for obj in objs]
    else:
        save_args = [(obj, None) for obj in objs]

    saved = db.save_many(save_args, overwrite=flags.f in options)

    if len(objs) == 1:
        return saved[0]

    return saved
