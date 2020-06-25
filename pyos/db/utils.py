from pyos import config
from pyos import os

__all__ = ('path_to_meta_dict',)


def new_meta(orig: dict, new: dict) -> dict:
    merged = new.copy()
    if not orig:
        return merged

    for name in config.KEYS:
        if name in orig:
            if name.startswith('_'):
                # Always take internal, i.e. underscored, keys
                merged[name] = orig[name]
            else:
                merged.setdefault(name, orig[name])

    return merged


def path_to_meta_dict(path: os.PathSpec) -> dict:
    """
    :param path: the path to get a dictionary for
    :return: the meta dictionary with the path
    """
    if path is None:
        return {}

    path = os.path.normpath(path)
    meta = {}
    if path.endswith(os.sep):
        meta[config.DIR_KEY] = path
    else:
        dirname, basename = os.path.split(path)
        meta[config.NAME_KEY] = basename
        if dirname:
            meta[config.DIR_KEY] = os.path.abspath(dirname)

    return meta
