# -*- coding: utf-8 -*-
from typing import Union, Iterable, Any

import pyos
from pyos import db
from pyos import psh


@pyos.psh_lib.command()
def load(*obj_or_ids) -> Union[Iterable[Any], Any]:
    """Load one or more objects"""
    _options, args = pyos.psh_lib.separate_opts(*obj_or_ids)
    if not args:
        return None

    # First load any by object id directly
    loaded = []
    rest = []
    hist = db.get_historian()
    for entry in args:
        if hist.is_obj_id(entry):
            try:
                loaded.append(hist.load(entry))
            except Exception as exc:  # pylint: disable=broad-except
                loaded.append(exc)
        else:
            rest.append(entry)

    # The remaining arguments are passed to ls which will try to find the corresponding objects
    to_load = psh.ls(*rest)  # pylint: disable=no-value-for-parameter
    for node in to_load:
        try:
            loaded.append(node.obj)
        except Exception as exc:  # pylint: disable=broad-except
            loaded.append(exc)

    if len(to_load) == 1:
        return loaded[0]

    return loaded
