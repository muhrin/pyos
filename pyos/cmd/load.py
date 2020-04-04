from typing import Union, Iterable, Any

import pyos
from .ls import ls
from . import flags


def load(*obj_or_ids) -> Union[Iterable[Any], Any]:
    """Load one or more objects"""
    _options, rest = pyos.opts.separate_opts(*obj_or_ids)
    to_load = ls(-flags.d, *rest)

    loaded = []
    for node in to_load:
        try:
            loaded.append(node.obj)
        except Exception as exc:  # pylint: disable=broad-except
            loaded.append(exc)

    if len(to_load) == 1:
        return loaded[0]

    return loaded