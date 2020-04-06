"""The locate command"""

from typing import Optional

import pyos
from pyos.psh_lib import opts
from pyos import psh


def locate(*obj_or_ids) -> Optional[pyos.fs.ResultsNode]:
    """Locate the directory of or more objects"""
    if not obj_or_ids:
        return None

    _options, rest = opts.separate_opts(*obj_or_ids)
    to_locate = psh.ls(-psh.d, *rest)
    to_locate.show('abspath', mode=pyos.fs.TABLE_VIEW)

    return to_locate
