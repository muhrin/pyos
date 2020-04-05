from typing import Union, Iterable, Any

from pyos import pysh
from pyos.shell import opts


def load(*obj_or_ids) -> Union[Iterable[Any], Any]:
    """Load one or more objects"""
    _options, rest = opts.separate_opts(*obj_or_ids)
    if not rest:
        return None

    to_load = pysh.ls(-pysh.d, *rest)

    loaded = []
    for node in to_load:
        try:
            loaded.append(node.obj)
        except Exception as exc:  # pylint: disable=broad-except
            loaded.append(exc)

    if len(to_load) == 1:
        return loaded[0]

    return loaded
