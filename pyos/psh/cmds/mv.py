"""The move command"""

import click

import pyos
from pyos import psh


@pyos.psh_lib.command(pass_options=True)
@pyos.psh_lib.flag(psh.f, help="Force - do not prompt before overwriting")
def mv(options, *args):  # pylint: disable=invalid-name
    """Take one or more files or directories with the final parameter being interpreted as
     destination

    mv has the following syntax, with the highlighted outcomes:

    Files as input:
    mv ('a', 'b/')  - move file 'a' into folder 'b/'
    mv ('a', 'b')   - rename file a to b

    Folders as input:
    mv ('a/', 'b/') - move folder 'a/' into folder 'b/' becoming 'b/a/'
    mv ('a/', 'b')  - rename folder 'a/' to be called 'b' having path 'b/'

    Multiple inputs:
    mv (*args, 'd')     - move all supplied *args to 'd/'
    mv (*args, 'd/')    - move all supplied *args to 'd/'

    For now, files will not be overwritten.
    """
    if len(args) < 2:
        raise ValueError("mv: missing destination")

    args = list(args)
    dest = pyos.Path(args.pop())

    if len(args) > 1:
        # If there is more than one thing to move then we assume that dest is a directory
        dest = dest.to_dir()

    to_move = psh.ls(-psh.d, *args)
    if dest.is_file_path():
        # Renaming
        if dest.exists():
            if -psh.f in options or click.confirm("Overwrite '{}'?".format(dest)):
                dest.unlink()
            else:
                return

        to_move[0].rename(dest.name)
    else:
        dest = dest.resolve()
        to_move.move(dest, overwrite=not options.pop(psh.n))
