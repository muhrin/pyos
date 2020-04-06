"""The remove command"""

import pyos
from pyos import psh


def rm(*obj_or_ids):  # pylint: disable=invalid-name
    """Remove objects"""
    _options, rest = pyos.psh_lib.separate_opts(*obj_or_ids)
    to_delete = psh.ls(-psh.d, *rest)
    for node in to_delete:
        node.delete()
