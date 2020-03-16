from pathlib import PurePosixPath
import typing

import mincepy

from .constants import DIR_KEY, NAME_KEY
from . import dirs
from . import opts
from . import sopts
from . import queries

__all__ = 'init', 'reset'


def init():
    dirs.init()


def reset():
    dirs.reset()


def get_records(path: [str, PurePosixPath] = None, type=None, meta=None):
    """Get the records in the given directory.  Use the current by default"""
    abspath = dirs.abspath(path)
    hist = mincepy.get_historian()

    meta_query = meta or {}
    meta_query.update(queries.dirmatch(dirs.dirstring(abspath)))
    return hist.find(obj_type=type, meta=meta_query, as_objects=False)


def locate(obj_or_ids):
    hist = mincepy.get_historian()
    directories = []
    for entry in obj_or_ids:
        obj_id = hist._ensure_obj_id(entry)
        meta = hist.meta.get(entry)
        directories.append(str(meta.get(DIR_KEY) / PurePosixPath(str(obj_id))))
    return directories


def get_ids(directory: [str, PurePosixPath] = None, type=None):
    """Get all obj ids in the directory"""
    return [record.obj_id for record in get_records(directory, type=type)]


def mv(path: PurePosixPath, obj_ids: typing.Iterable):
    hist = mincepy.get_historian()
    abspath = dirs.abspath(path)

    update = dirs.dirstring(dirs.dirstring(abspath))
    for obj_id in obj_ids:
        hist.meta.update(obj_id, update)


def get_meta(*obj_ids: typing.Iterable) -> typing.List[dict]:
    """Get the metadata for a bunch of objects"""
    hist = mincepy.get_historian()
    meta = []
    for obj_id in obj_ids:
        meta.append(hist.meta.get(obj_id))
    return meta


def update_meta(*obj_ids: typing.Iterable, meta: dict):
    """Update the metadata for a bunch of objects"""
    hist = mincepy.get_historian()
    for obj_id in obj_ids:
        hist.meta.update(obj_id, meta)


def set_meta(*obj_ids: typing.Iterable, meta: dict):
    """Set the metadata for a bunch of objects"""
    hist = mincepy.get_historian()
    for obj_id in obj_ids:
        hist.meta.set(obj_id, meta)


def set_name(obj_id, name: str):
    """Set the name of the passed object(s)"""
    hist = mincepy.get_historian()
    update = {NAME_KEY: name}
    hist.meta.update(obj_id, update)


def find(*args, **meta_filter) -> typing.Iterable:
    options, starting_point = opts.separate_opts(*args)

    min_depth = opts.extract_val(sopts.mindepth, options, 0)
    max_depth = opts.extract_val(sopts.maxdepth, options, -1)

    if starting_point:
        spoints = [dirs.dirstring(dirs.abspath(path)) for path in starting_point]
    else:
        spoints = [dirs.dirstring(dirs.cwd())]

    meta_filter = meta_filter or {}

    meta_filter.update(
        queries.or_(*(queries.subdirs(point, min_depth, max_depth) for point in spoints)))

    hist = mincepy.get_historian()
    metas = hist.meta.find(meta_filter)

    return set(meta['obj_id'] for meta in metas)


init()  # by importing this module we initialise
