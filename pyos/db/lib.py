from collections import abc
import getpass
from typing import Sequence, Iterable, Optional, Tuple, Any, Union, Iterator

import deprecation
import mincepy

from pyos import config
from pyos import exceptions
from pyos import os
from pyos import version
from . import utils

__all__ = ('get_historian', 'get_meta', 'update_meta', 'set_meta', 'find_meta', 'save_one',
           'save_many', 'get_abspath', 'load', 'to_obj_id', 'get_obj_id', 'init', 'reset',
           'get_path', 'get_paths', 'rename', 'homedir', 'connect', 'get_oid',
           'get_obj_id_from_path')

_HISTORIAN = None  # type: Optional[mincepy.Historian]


def connect(uri: str = '') -> mincepy.Historian:
    mincepy.connect(uri, use_globally=True)
    return init()


def init():
    # Make sure the indexes are there
    global _HISTORIAN  # pylint: disable=global-statement
    historian = mincepy.get_historian()
    if historian is _HISTORIAN:
        return historian

    historian.meta.create_index([
        (config.NAME_KEY, mincepy.ASCENDING),
        (config.DIR_KEY, mincepy.ASCENDING),
    ],
                                unique=True,
                                where_exist=True)
    historian.meta.create_index(config.NAME_KEY, unique=False, where_exist=True)
    historian.meta.create_index(config.DIR_KEY, unique=False, where_exist=True)

    # Set the current path
    path = '/{}/'.format(getpass.getuser())
    historian.meta.sticky[config.DIR_KEY] = path

    # All done
    _HISTORIAN = historian
    return historian


def get_historian():
    """Get the active historian in pyos"""
    global _HISTORIAN  # pylint: disable=global-statement
    historian = mincepy.get_historian(create=False)
    if historian is not None and historian is not _HISTORIAN:
        raise RuntimeError("PyOS has not been initialised with the current historian.  "
                           "Call pyos.db.init()")
    return _HISTORIAN


def reset():
    global _HISTORIAN  # pylint: disable=global-statement
    if _HISTORIAN is not None:
        _HISTORIAN.meta.sticky.pop(config.DIR_KEY, None)
        _HISTORIAN = None


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


# endregion

# region paths


def get_path(obj_or_id) -> Optional[str]:
    """Given an object or object id get the current path"""
    return get_paths(obj_or_id)[0]


def get_paths(*obj_or_id) -> Sequence[Optional[str]]:
    """Given objects or identifier this will return their current paths in the order they were
    passed"""
    hist = get_historian()
    obj_ids = tuple(map(hist.get_obj_id, obj_or_id))
    metas = dict(hist.meta.find({}, obj_id=obj_ids))
    paths = []
    for obj_id in obj_ids:
        meta = metas.pop(obj_id)
        dirname, name = meta.get(config.DIR_KEY, None), meta.get(config.NAME_KEY, None)
        path = []
        if dirname:
            path.append(dirname)
        path.append(name or str(obj_id))

        paths.append(os.path.join(*path))

    return paths


def rename(obj_or_id, dest: os.PathSpec):
    """Rename an object to a the dest.  If dest is is a directory IsADirectoryError is raised."""
    dest = os.fspath(dest)
    if dest.endswith(os.sep):
        raise exceptions.IsADirectoryError(dest)

    hist = get_historian()
    obj_id = hist.to_obj_id(obj_or_id)
    hist.meta.update(obj_id, meta=utils.path_to_meta_dict(dest))


def get_abspath(obj_id, meta: dict) -> str:
    """Given an object id and metadata dictionary this method will return a string representing
    the absolute path of the object"""
    assert obj_id, "Must provide a valid obj id"
    dirname = meta[config.DIR_KEY]
    basename = meta.get(config.NAME_KEY, str(obj_id))
    return os.path.join(dirname, basename)


def homedir(user: str = '') -> str:
    """Return the user's home directory"""
    if not user:
        user_info = get_historian().get_user_info()
        user_name = user_info[mincepy.ExtraKeys.USER]
    else:
        user_name = user
    return "/{}/".format(user_name)


# endregion


def save_one(obj, path: os.PathSpec = None, overwrite=False, historian=None):
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
            path = os.getcwd()

    meta = None
    if path is not None:
        path = os.path.abspath(path)
        meta = utils.path_to_meta_dict(path)

    try:
        return hist.save_one(obj, meta=meta)
    except mincepy.DuplicateKeyError:
        if overwrite:
            os.remove(path)
            # Try again
            return hist.save_one(obj, meta=meta)

        raise


def save_many(to_save: Iterable[Union[Any, Tuple[Any, os.PathSpec]]],
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
        if isinstance(entry, abc.Sequence):
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


def to_obj_id(identifier):
    """Get the database object id from the passed identifier.  If the identifier is already a
    mincePy object id it will be returned unaltered.  Otherwise mincePy will try and turn the type
    into an object id.  It it fails, None is returned"""
    return get_historian().to_obj_id(identifier)


@deprecation.deprecated(deprecated_in="0.7.10",
                        removed_in="0.8.0",
                        current_version=version.__version__,
                        details="Use next(get_obj_id_from_path()) instead")
def get_obj_id(path: os.PathSpec):
    """Given a path get the id of the corresponding object.  Returns None if not found."""
    return next(get_obj_id_from_path(path))


def get_obj_id_from_path(*path: os.PathSpec) -> Iterator:
    """Given a path get the id of the corresponding object.  Returns None if not found."""
    for entry in path:
        entry = os.fspath(entry)

        # Check if the basename is an object id
        basename = os.path.basename(entry)
        if basename:
            hist = get_historian()
            try:
                yield hist.archive.construct_archive_id(basename)
                continue
            except ValueError:
                pass

        results = find_meta(utils.path_to_meta_dict(entry))
        try:
            yield next(results)[0]
        except StopIteration:
            yield None


def get_oid(*identifier) -> Iterator:
    """Get one or more object ids.

    :param identifier: can be any of the following:
        * an object id
        * an object instance
        * a string representing a valid object id
        * the path to an object
        these will be tested in order in an attempt to get the object id.  If all fail then None
        will be yielded.
    """
    hist = get_historian()

    for ident in identifier:
        obj_id = None

        if ident is not None:
            # Let the historian try to interpret it, no db access
            obj_id = hist.to_obj_id(ident)

            if obj_id is None:
                # Maybe it is a path
                try:
                    path = os.fspath(ident)
                except TypeError:
                    pass
                else:
                    obj_id = next(get_obj_id_from_path(path))  # pylint: disable=stop-iteration-return

        yield obj_id
