from pathlib import PurePosixPath
import typing

import mincepy

from .constants import DIR_KEY, NAME_KEY
from . import dirs
from . import query

__all__ = 'init', 'reset'


def init():
    dirs.init()


def reset():
    dirs.reset()


def get_contents(directory: [str, PurePosixPath] = None, type=None, meta=None, as_objects=False):
    """Get the content of the given directory.  Use the current by default"""
    path = dirs.getpath(directory)
    hist = mincepy.get_historian()

    meta_query = meta or {}
    meta_query.update({DIR_KEY: dirs.dirstring(path)})
    return hist.find(obj_type=type, meta=meta_query, as_objects=as_objects)


def find(directory: [str, PurePosixPath] = None, type=None, meta=None, as_objects=False):
    """Get the content of the given directory.  Use the current by default"""
    path = dirs.getpath(directory)
    hist = mincepy.get_historian()

    meta_query = meta or {}
    meta_query.update({DIR_KEY: dirs.dirstring(path)})
    return hist.find(obj_type=type, meta=meta_query, as_objects=as_objects)


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
    return [record.obj_id for record in get_contents(directory, type=type)]


def mv(destination: PurePosixPath, obj_ids: typing.Iterable):
    hist = mincepy.get_historian()
    path = dirs.abspath(destination)

    update = {DIR_KEY: dirs.dirstring(path)}
    for obj_id in obj_ids:
        hist.meta.update(obj_id, update)


def set_meta(obj_ids: typing.Iterable, meta: dict):
    """Set the metadata for a bunch of objects"""
    hist = mincepy.get_historian()
    for obj_id in obj_ids:
        hist.meta.update(obj_id, meta)


def get_meta(obj_ids: typing.Iterable) -> typing.List[dict]:
    """Get the metadata for a bunch of objects"""
    hist = mincepy.get_historian()
    meta = []
    for obj_id in obj_ids:
        meta.append(hist.meta.get(obj_id))
    return meta


def set_name(obj_id, name: str):
    """Set the name of the passed object(s)"""
    hist = mincepy.get_historian()
    update = {NAME_KEY: name}
    hist.meta.update(obj_id, update)


def find_ids(*starting_point, **meta_filter):
    starting_point = starting_point or [dirs.get_directory()]
    meta_filter = meta_filter or {}

    meta_filter.update({
        '$or': [
            query.subdirs(dirs.dirstring(dirs.abspath(point)), 0, 0) for point in starting_point
        ]
    })

    hist = mincepy.get_historian()
    metas = hist.meta.find(meta_filter)

    return set(meta['obj_id'] for meta in metas)
