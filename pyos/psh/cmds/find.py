"""The find command"""
import argparse

import cmd2

import pyos
from pyos.psh import base


@pyos.psh_lib.command()
def find(
        *starting_point: pyos.os.PathLike,
        meta: dict = None,
        state: dict = None,
        type=None,  # pylint: disable=redefined-builtin
        mindepth=0,
        maxdepth=-1) -> pyos.fs.ResultsNode:
    """Find objects matching the given criteria, optionally starting from one or more paths


    :param starting_point: one or more paths to start the search from
    :param meta: a dictionary for the metadata to match
    :param state: a dictionary for the record state to match
    :param type: restrict the match to objects of this type
    :param mindepth: the minimum depth to search at relative to the start point(s)
    :param maxdepth: the maximum depth to search at relative to the start point(s)
    """
    _options, spoints = pyos.psh_lib.opts.separate_opts(*starting_point)
    if not spoints:
        spoints = (pyos.pathlib.Path(),)

    return pyos.fs.find(*spoints,
                        meta=meta,
                        state=state,
                        type=type,
                        mindepth=mindepth,
                        maxdepth=maxdepth)


parser = argparse.ArgumentParser()  # pylint: disable=invalid-name
parser.add_argument('path', nargs='*', type=str, completer_method=base.BaseShell.file_completer)


@cmd2.with_argparser(parser)
def do_find(app: cmd2.Cmd, args):
    command = find

    app.poutput(command(*args.path))
