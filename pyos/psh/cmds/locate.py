"""The locate command"""

from typing import Optional, Union, Sequence

import pyos
from pyos import psh


@pyos.psh_lib.command()
def locate(*obj_or_ids) -> Optional[Union[pyos.pathlib.Path, Sequence[pyos.pathlib.Path]]]:
    """Locate the directory of one or more objects"""
    if not obj_or_ids:
        return None

    to_locate = psh.ls(-psh.d, *obj_or_ids)
    # Convert to abspaths
    paths = [node.abspath for node in to_locate]
    results = pyos.psh_lib.CachingResults(paths.__iter__(), representer=str)

    if len(obj_or_ids) == 1:
        return results[0]

    return results
