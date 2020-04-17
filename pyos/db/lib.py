import getpass
from typing import Sequence, Iterable, Optional, Tuple, Any, Union

import mincepy

import pyos
from . import queries
from . import utils

__all__ = ('get_historian', 'get_meta', 'update_meta', 'set_meta', 'find_meta', 'set_name',
           'save_one', 'save_many', 'get_abspath', 'load', 'to_obj_id', 'get_obj_id', 'init',
           'reset')


def get_historian():
    """Get the active historian in pyos"""
    return mincepy.get_historian()


def init():
    mincepy.get_historian().meta.create_index([
        (pyos.config.NAME_KEY, mincepy.ASCENDING),
        (pyos.config.DIR_KEY, mincepy.ASCENDING),
    ],
                                              unique=True,
                                              where_exist=True)
    path = '/{}/'.format(getpass.getuser())
    get_historian().meta.sticky[pyos.config.DIR_KEY] = path


def reset():
    get_historian().meta.sticky.pop(pyos.config.DIR_KEY, None)


# region metadata


def get_meta(obj_id: Union[Any, Iterable[Any]]):
    """Get the metadata for a bunch of objects"""
    hist = get_historian()
    return hist.archive.meta_get(obj_id)


def update_meta(*obj_or_identifier: Iterable, meta: dict):
    """Update the metadata for a bunch of objects"""
    hist = get_historian()
    for obj_id in obj_or_identifier:
        hist.meta.update(obj_id, meta)


def set_meta(*obj_or_identifier: Iterable, meta: dict):
    """Set the metadata for a bunch of objects"""
    hist = get_historian()
    obj_ids = tuple(map(to_obj_id, obj_or_identifier))
    metas = dict(find_meta(obj_ids=obj_ids))

    # Preserve the internal keys
    for obj_id in obj_ids:
        new_meta = utils.new_meta(metas.get(obj_id, {}), meta)
        hist.meta.set(obj_id, new_meta)


def find_meta(filter: dict = None, obj_ids=None):  # pylint: disable=redefined-builtin
    filter = filter or {}
    hist = get_historian()
    return hist.meta.find(filter, obj_ids)


def set_name(*obj_ids, name: str):
    """Set the name of the passed object(s)"""
    update = {pyos.config.NAME_KEY: name}
    update_meta(*obj_ids, meta=update)


def get_name(*obj_or_ids) -> Sequence[Optional[str]]:
    """Get the name of the passed objects(s)"""
    hist = get_historian()
    results = hist.meta.find({'obj_id': queries.in_(*obj_or_ids)})
    names = {meta['obj_id']: meta[pyos.config.NAME_KEY] for meta in results}
    return [names.get(obj_id, None) for obj_id in obj_or_ids]


# endregion


def save_one(obj, path: pyos.os.PathSpec = None, overwrite=False, historian=None):
    """Save one object to a the given path.  The path can be a filename or a directory or a filename
    in a directory

    :param obj: the object to save
    :param path: the optional path to save it to
    :param overwrite: overwrite if there is already an object at that path
    """
    hist = historian or get_historian()

    if path is None:
        # Check if it's already saved (in which case we don't need to set a path)
        if hist.get_obj_id(obj) is None:
            path = './'

    meta = None
    if path is not None:
        path = pyos.os.path.abspath(path)
        meta = utils.path_to_meta_dict(path)

    try:
        return hist.save_one(obj, meta=meta)
    except mincepy.DuplicateKeyError:
        if overwrite:
            pyos.os.remove(path)
            # Try again
            return hist.save_one(obj, meta=meta)

        raise


def save_many(to_save: Iterable[Union[Any, Tuple[Any, pyos.os.PathSpec]]],
              overwrite=False,
              historian=None):
    """
    Save many objects, expects an iterable where each entry is an object to save or a tuple of
    length 2 containing the object and a path of where to save it.

    :param to_save: the iterable able objects to save
    :param overwrite: overwrite objects with the same name
    """
    obj_ids = []
    for entry in to_save:
        path = None
        if isinstance(entry, Sequence):
            if len(entry) > 2:
                raise ValueError("Can only pass sequences of at most length 2")
            obj, path = entry[0], entry[1]
        else:
            # Assume it's just the object
            obj = entry
        obj_ids.append(save_one(obj, path, overwrite, historian=historian))

    return obj_ids


def load(*identifier):
    """Load one or more objects"""
    get_historian().load(*identifier)


def get_abspath(obj_id, meta: dict) -> str:
    """Given an object id and metadata dictionary this method will return a string representing
    the absolute path of the object

    :rtype: pyos.pathlib.Path
    """
    assert obj_id, "Must provide a valid obj id"
    dirname = meta[pyos.config.DIR_KEY]
    basename = meta.get(pyos.config.NAME_KEY, str(obj_id))
    return pyos.os.path.join(dirname, basename)


def to_obj_id(identifier):
    """Get the database object id from the passed identifier.  If the identifier is already a
    mincepy object id it will be returned unaltered.  Otherwise mincepy will try and turn the type
    into an object id.  It it fails, None is returned"""
    return get_historian().to_obj_id(identifier)


def get_obj_id(path: pyos.os.PathSpec):
    """Given a path get the id of the corresponding object.  Returns None if not found."""
    results = find_meta(utils.path_to_meta_dict(path))
    try:
        return next(results)[0]
    except StopIteration:
        return None
