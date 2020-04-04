"""The locate command"""

import pyos
from .ls import ls
from . import flags


def locate(*obj_or_ids) -> pyos.ResultsNode:
    """Locate the directory of or more objects"""
    _options, rest = pyos.opts.separate_opts(*obj_or_ids)
    to_locate = ls(-flags.d, *rest)
    to_locate.show('abspath', mode=pyos.TABLE_VIEW)

    return to_locate
