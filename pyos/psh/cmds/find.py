"""The find command"""
import argparse

import cmd2
from mincepy import qops

import pyos
from pyos.psh import argparse_types
from pyos.psh import completion

__all__ = ('find',)


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


class Find(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t',
                        dest='type',
                        type=argparse_types.type_string,
                        help="the type to search for")
    parser.add_argument('-s',
                        dest='paths',
                        action='append',
                        type=str,
                        default=[],
                        completer_method=completion.dir_completer,
                        help="starting point (path) for search")
    parser.add_argument('-m',
                        dest='meta',
                        action='append',
                        type=argparse_types.parse_query,
                        help='a constraint to apply to the metadata')
    parser.add_argument('--maxdepth',
                        dest='maxdepth',
                        type=int,
                        default=-1,
                        help='maximum depth to search at relative to starting point(s) '
                        '(-1 means no maximum)')
    parser.add_argument('--mindepth',
                        dest='mindepth',
                        type=int,
                        default=0,
                        help='minimum depth to start search at relative to starting point(s)')
    parser.add_argument('state',
                        type=argparse_types.parse_query,
                        nargs='*',
                        help='a constraint to apply to the state of the object')

    @cmd2.with_argparser(parser)
    def do_find(self, args):  # pylint: disable=no-self-use
        meta = None
        state = None
        if args.meta:
            meta = qops.and_(*args.meta)
        if args.state:
            state = qops.and_(*args.state)

        res = pyos.fs.find(*args.paths,
                           type=args.type,
                           meta=meta,
                           state=state,
                           mindepth=args.mindepth,
                           maxdepth=args.maxdepth)
        print(res)
