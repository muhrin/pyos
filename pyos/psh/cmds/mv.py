"""The move command"""

import pyos
from pyos import psh


@pyos.psh_lib.command(pass_options=True)
@pyos.psh_lib.flag(psh.n, help="No clobber - don't overwrite if the same filename exists")
def mv(options, *args):  # pylint: disable=invalid-name
    """Take one or more files or directories with the final parameter being interpreted as
     destination"""
    if len(args) < 2:
        raise ValueError("mv: missing destination")

    args = list(args)
    dest = pyos.pathlib.Path(args.pop())
    if len(args) > 1:
        # If there is more than one thing to move then we assume that dest is a directory
        dest = dest.to_dir()
    dest = dest.resolve()
    to_move = psh.ls(-psh.d, *args)
    to_move.move(dest, overwrite=not options.pop(psh.n))
