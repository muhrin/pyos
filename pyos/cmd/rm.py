"""The remove command"""

import pyos
from .ls import ls
from . import flags


def rm(*obj_or_ids):  # pylint: disable=invalid-name
    """Remove objects"""
    _options, rest = pyos.opts.separate_opts(*obj_or_ids)
    to_delete = ls(-flags.d, *rest)
    for node in to_delete:
        node.delete()
