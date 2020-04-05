"""The remove command"""

import pyos
from pyos import pysh


def rm(*obj_or_ids):  # pylint: disable=invalid-name
    """Remove objects"""
    _options, rest = pyos.shell.separate_opts(*obj_or_ids)
    to_delete = pysh.ls(-pysh.d, *rest)
    for node in to_delete:
        node.delete()
