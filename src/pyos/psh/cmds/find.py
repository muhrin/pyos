"""The find command"""

import argparse
import functools
import operator
import os as std_os

import cmd2
import mincepy
from mincepy import qops

from ... import fs, os, pathlib, psh_lib
from .. import argparse_types, completion

__all__ = ("find",)


@psh_lib.command()
def find(
    *args,
    meta: dict = None,
    state: dict = None,
    type=None,
    mindepth=0,
    maxdepth=-1,
) -> fs.ResultsNode:
    """Find objects matching the given criteria, optionally starting from one or more paths, e.g.::

        find("/home/", Person.name == "mark")

    :param args: the paths to start the search from (strings, paths or filesystem nodes), and any
        filters that objects must match.  Anything that isn't a path is passed on to mincePy (see
        :func:`mincepy.build_expr`) so all of its filter expressions can be used, and if several
        are given objects must match all of them.
    :param meta: a dictionary for the metadata to match
    :param state: a dictionary for the record state to match
    :param type: restrict the match to objects of this type
    :param mindepth: the minimum depth to search at relative to the start point(s)
    :param maxdepth: the maximum depth to search at relative to the start point(s)
    """
    _options, rest = psh_lib.opts.separate_opts(*args)
    spoints, filters = _split_args(rest)
    if not spoints:
        spoints = [pathlib.Path()]

    return fs.find(
        *spoints,
        meta=meta,
        state=state,
        type=type,
        obj_filter=functools.reduce(operator.and_, filters) if filters else None,
        mindepth=mindepth,
        maxdepth=maxdepth,
    )


def _split_args(args) -> tuple[list, list[mincepy.Expr]]:
    """Split the arguments into the starting points (paths) and the filters, anything that isn't a
    path is given to mincePy to interpret"""
    spoints = []
    filters = []
    for arg in args:
        if isinstance(arg, (str, os.PathLike)):
            spoints.append(arg)
        elif isinstance(arg, fs.nodes.FilesystemNode):
            spoints.append(arg.abspath)
        elif isinstance(arg, std_os.PathLike):
            spoints.append(std_os.fspath(arg))
        else:
            filters.append(mincepy.build_expr(arg))

    return spoints, filters


class Find(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        dest="type",
        type=argparse_types.type_string,
        help="the type to search for",
    )
    parser.add_argument(
        "-s",
        dest="paths",
        action="append",
        type=str,
        default=[],
        completer=completion.dir_completer,
        help="starting point (path) for search",
    )
    parser.add_argument(
        "-m",
        dest="meta",
        action="append",
        type=argparse_types.parse_query,
        help="a constraint to apply to the metadata",
    )
    parser.add_argument(
        "--maxdepth",
        dest="maxdepth",
        type=int,
        default=-1,
        help="maximum depth to search at relative to starting point(s) (-1 means no maximum)",
    )
    parser.add_argument(
        "--mindepth",
        dest="mindepth",
        type=int,
        default=0,
        help="minimum depth to start search at relative to starting point(s)",
    )
    parser.add_argument(
        "state",
        type=argparse_types.parse_query,
        nargs="*",
        help="a constraint to apply to the state of the object",
    )

    @cmd2.with_argparser(parser)
    def do_find(self, args):
        meta = None
        state = None
        if args.meta:
            meta = qops.and_(*args.meta)
        if args.state:
            state = qops.and_(*args.state)

        res = fs.find(
            *args.paths,
            type=args.type,
            meta=meta,
            state=state,
            mindepth=args.mindepth,
            maxdepth=args.maxdepth,
        )

        res.__stream_out__(self._cmd.stdout)
