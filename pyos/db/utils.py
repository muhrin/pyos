# -*- coding: utf-8 -*-
from typing import Optional

import deprecation

from pyos import config
from pyos import os
from pyos import version

__all__ = 'path_to_meta_dict', 'get_obj_name', 'path_from_meta_entry'


@deprecation.deprecated(deprecated_in='0.8.0',
                        removed_in='0.9.0',
                        current_version=version.__version__,
                        details='No longer use metadata to store filesystem location')
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


@deprecation.deprecated(deprecated_in='0.8.0',
                        removed_in='0.9.0',
                        current_version=version.__version__,
                        details='No longer use metadata to store filesystem location')
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


@deprecation.deprecated(deprecated_in='0.8.0',
                        removed_in='0.9.0',
                        current_version=version.__version__,
                        details='No longer use metadata to store filesystem location')
def path_from_meta_entry(obj_id, meta: dict) -> Optional[str]:
    parts = []
    if config.DIR_KEY in meta:
        parts.append(meta[config.DIR_KEY])
    if config.NAME_KEY in meta:
        parts.append(meta[config.NAME_KEY])
    else:
        parts.append(str(obj_id))

    if not parts:
        return None

    return ''.join(parts)


@deprecation.deprecated(deprecated_in='0.8.0',
                        removed_in='0.9.0',
                        current_version=version.__version__,
                        details='No longer use metadata to store filesystem location')
def get_obj_name(obj_id, meta: dict) -> str:
    """Get the name of an object.  This will be the name that is used to represent this object on
    the virtual filesystem and is stored in the metadata"""
    return meta.get(config.NAME_KEY, str(obj_id))
