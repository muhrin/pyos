import typing

import mincepy

from .constants import NAME_KEY, DIR_KEY
from . import dirs
from . import nodes
from . import queries
from . import utils

__all__ = 'init', 'reset'

from .dirs import path_to_meta_dict


def init():
    mincepy.get_historian().meta.create_index([
        (NAME_KEY, mincepy.ASCENDING),
        (DIR_KEY, mincepy.ASCENDING),
    ],
                                              unique=True,
                                              where_exist=True)
    dirs.init()


def reset():
    dirs.reset()


# region metadata


def get_meta(*obj_or_identifier: typing.Iterable) -> typing.List[dict]:
    """Get the metadata for a bunch of objects"""
    hist = mincepy.get_historian()
    meta = []
    for obj_id in obj_or_identifier:
        meta.append(hist.meta.get(obj_id))
    return meta


def update_meta(*obj_or_identifier: typing.Iterable, meta: dict):
    """Update the metadata for a bunch of objects"""
    hist = mincepy.get_historian()
    for obj_id in obj_or_identifier:
        hist.meta.update(obj_id, meta)


def set_meta(*obj_or_identifier: typing.Iterable, meta: dict):
    """Set the metadata for a bunch of objects"""
    hist = mincepy.get_historian()
    metas = [hist.meta.get(value) for value in obj_or_identifier]

    # Convert to a list because get() will give us a scalar if we pass a single object id
    if len(obj_or_identifier) == 1:
        metas = [metas]

    # Preserve the internal keys
    for obj_id, current_meta in zip(obj_or_identifier, metas):
        new_meta = utils.new_meta(current_meta, meta)
        hist.meta.set(obj_id, new_meta)


def set_name(*obj_ids, name: str):
    """Set the name of the passed object(s)"""
    update = {NAME_KEY: name}
    update_meta(*obj_ids, meta=update)


def get_name(*obj_or_ids) -> typing.Sequence[typing.Optional[str]]:
    """Get the name of the passed objects(s)"""
    hist = mincepy.get_historian()
    results = hist.meta.find({'obj_id': {'$in': obj_or_ids}})
    names = {meta['obj_id']: meta[NAME_KEY] for meta in results}
    return [names.get(obj_id, None) for obj_id in obj_or_ids]


# endregion


def save(objects: typing.Sequence, paths: typing.Sequence[dirs.PathSpec] = None):
    if paths is None:
        metas = [None] * len(objects)
    else:
        assert len(objects) == len(paths), "Must supply equal number of objects and paths"
        metas = [path_to_meta_dict(path) for path in paths]

    if len(objects) == 1:
        metas = metas[0]

    return mincepy.get_historian().save(*objects, with_meta=metas)


def find(
        *starting_point,
        meta: dict = None,
        state: dict = None,
        type=None,  # pylint: disable=redefined-builtin
        mindepth=0,
        maxdepth=-1) -> nodes.ResultsNode:
    """
    Find objects matching the given criteria

    :param starting_point: the starting points for the search, if not supplied defaults to '/'
    :param meta: filter criteria for the metadata
    :param state: filter criteria for the object's saved state
    :param type: restrict the search to this type (can be a tuple of types)
    :param mindepth: the minimum depth from the starting point(s) to search in
    :param maxdepth: the maximum depth from the starting point(s) to search in
    :return: results node
    """
    if not starting_point:
        starting_point = (dirs.PyosPath('/'),)
    if meta is None:
        meta = {}
    if state is None:
        state = {}

    if starting_point:
        spoints = [str(dirs.PyosPath(path).resolve()) for path in starting_point]
    else:
        spoints = [str(dirs.cwd())]

    # Add the directory search criteria to the meta search
    meta.update(queries.or_(*(queries.subdirs(point, mindepth, maxdepth) for point in spoints)))

    hist = mincepy.get_historian()

    # Find the metadata
    metas = {}
    for result in hist.meta.find(meta):
        metas[result['obj_id']] = result

    data = {}
    if metas and (type is not None or state is not None):
        # Further restrict the match
        meta_filter = {'obj_id': queries.in_(*metas.keys())}
        for entry in hist.find(obj_type=type, state=state, meta=meta_filter, as_objects=False):
            data[entry.obj_id] = dict(record=entry, meta=metas[entry.obj_id])

    results = nodes.ResultsNode()
    for obj_id, entry in data.items():
        node = nodes.ObjectNode(obj_id,
                                record=entry.get('record', None),
                                meta=entry.get('meta', None))
        results.append(node)
    return results
