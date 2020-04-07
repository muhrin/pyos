"""The move command"""

import pyos
from pyos import psh


@pyos.psh_lib.flag(psh.n, help="No clobber - don't overwrite if the same filename exists")
def mv(*args):  # pylint: disable=invalid-name
    """Take one or more files or directories with the final parameter being interpreted as
     destination"""
    options = args[0]
    rest = list(args[1:])
    assert len(rest) <= 2, "mv: missing destination"
    dest = pyos.pathlib.Path(rest.pop())
    if len(rest) > 1:
        # If there is more than one thing to move then we assume that dest is a directory
        dest = dest.to_dir()
    dest = dest.resolve()
    to_move = psh.ls(-psh.d, *rest)
    to_move.move(dest, overwrite=not options.pop(psh.n))
