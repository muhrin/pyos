"""The move command"""
import argparse

import click
import cmd2

import pyos
from pyos import psh
from pyos.psh import completion


@pyos.psh_lib.command(pass_options=True)
@pyos.psh_lib.flag(psh.f, help="force - do not prompt before overwriting")
def mv(options, *args):  # pylint: disable=invalid-name
    """Take one or more files or directories with the final parameter being interpreted as
     destination

    mv has the following syntax, with the indicated outcomes:

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


class Mv(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', action='store_true', help="force - do not prompt before overwriting")
    parser.add_argument('path', nargs='*', type=str, completer_method=completion.path_complete)

    @cmd2.with_argparser(parser)
    def do_mv(self, args):  # pylint: disable=no-self-use
        command = mv
        if args.f:
            command = command - psh.f

        print(command(*args.path))
