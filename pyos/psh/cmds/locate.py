"""The locate command"""

from typing import Optional

import pyos
from pyos import psh


@pyos.psh_lib.command()
def locate(*obj_or_ids) -> Optional[pyos.fs.ResultsNode]:
    """Locate the directory of or more objects"""
    if not obj_or_ids:
        return None

    to_locate = psh.ls(-psh.d, *obj_or_ids)
    to_locate.show('abspath', mode=pyos.fs.TABLE_VIEW)

    return to_locate
