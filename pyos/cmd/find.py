"""The find command"""

import pyos


def find(
        *starting_point,
        meta: dict = None,
        state: dict = None,
        type=None,  # pylint: disable=redefined-builtin
        mindepth=0,
        maxdepth=-1) -> pyos.ResultsNode:
    _options, spoints = pyos.opts.separate_opts(*starting_point)
    if not spoints:
        spoints = (pyos.dirs.cwd(),)

    return pyos.lib.find(*spoints,
                         meta=meta,
                         state=state,
                         type=type,
                         mindepth=mindepth,
                         maxdepth=maxdepth)
