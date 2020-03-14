import typing

import mincepy

from . import dirs


def expand_to_obj_ids(identifiers: typing.Iterable) -> typing.Iterable:
    """Given an iterable of entries expand these to a flat container of object ids.

    The entries can be of type (in order of priority):
    1. An object id which remains unchanged
    2. A string containing only whitespace and '*' will resolve to all entries in current directory
    3. A string which will be interpreted as an object id
    4. A saved object, in which case it's obj_id will be retrieved
    5. A container containing entries of any of these types which will be expanded recursively
    """
    expanded = []

    hist = mincepy.get_historian()
    for entry in identifiers:
        if hist.is_obj_id(entry):
            expanded.append(entry)
            continue

        if isinstance(entry, str) and entry.strip() == '*':
            expanded.extend(dirs.get_contents()[0].keys())
            continue

        if isinstance(entry, str):
            obj_id = get_obj_id(entry)
            if obj_id is not None:
                expanded.append(obj_id)
                continue

        obj_id = hist.get_obj_id(entry)
        if obj_id is not None:
            expanded.append(obj_id)
            continue

        if not isinstance(entry, str) and isinstance(entry, typing.Iterable):
            expanded.extend(expand_to_obj_ids(entry))
            continue

        raise TypeError("Unsupported expansion type: {}".format(type(entry)))

    return expanded


def get_obj_id(entity):
    # First see if the historian can identify it
    hist = mincepy.get_historian()
    try:
        return hist._ensure_obj_id(entity)
    except mincepy.NotFound:
        pass

    # Then maybe it's a objname
    return dirs.get_obj_id(entity)
