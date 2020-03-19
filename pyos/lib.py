import typing

import mincepy

from .constants import NAME_KEY
from . import dirs
from . import nodes
from . import opts
from . import sopts
from . import queries

__all__ = 'init', 'reset'

from .dirs import path_to_meta_dict


def init():
    dirs.init()


def reset():
    dirs.reset()


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


def get_name(*obj_or_ids) -> typing.Sequence[typing.Optional[str]]:
    """Get the name of the passed objects(s)"""
    hist = mincepy.get_historian()
    results = hist.meta.find({'obj_id': {'$in': obj_or_ids}})
    names = {meta['obj_id']: meta[NAME_KEY] for meta in results}
    return [names.get(obj_id, None) for obj_id in obj_or_ids]


def save(objects: typing.Sequence, paths: typing.Sequence[dirs.PathSpec] = None):
    if paths is None:
        metas = [None] * len(objects)
    else:
        assert len(objects) == len(paths), "Must supply equal number of objects and paths"
        metas = [path_to_meta_dict(path) for path in paths]

    if len(objects) == 1:
        metas = metas[0]

    return mincepy.get_historian().save(*objects, with_meta=metas)


def find(*args, **meta_filter) -> nodes.ResultsNode:
    options, starting_point = opts.separate_opts(*args)

    min_depth = options.pop(sopts.mindepth, 0)
    max_depth = options.pop(sopts.maxdepth, -1)

    if starting_point:
        spoints = [str(dirs.PyosPath(path).resolve()) for path in starting_point]
    else:
        spoints = [str(dirs.cwd())]

    meta_filter = meta_filter or {}

    meta_filter.update(
        queries.or_(*(queries.subdirs(point, min_depth, max_depth) for point in spoints)))

    hist = mincepy.get_historian()
    metas = hist.meta.find(meta_filter)

    results = nodes.ResultsNode()
    for meta in metas:
        results.append(nodes.ObjectNode(meta['obj_id']))

    return results
