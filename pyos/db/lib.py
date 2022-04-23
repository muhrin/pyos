# -*- coding: utf-8 -*-
import collections
from typing import Sequence, Iterable, Optional, Tuple, Any, Union, Iterator

import deprecation
import mincepy
from tqdm import tqdm

from pyos import exceptions
from pyos import os
from pyos import version
from . import database
from . import fs

__all__ = ('get_meta', 'update_meta', 'set_meta', 'find_meta', 'save_one', 'save_many',
           'get_abspath', 'load', 'to_obj_id', 'get_obj_id', 'get_path', 'get_paths', 'rename',
           'homedir', 'get_oid', 'get_obj_id_from_path', 'set_path', 'set_paths')

# region metadata


def get_meta(obj_id: Union[Any, Iterable[Any]]):
    """Get the metadata for a bunch of objects"""
    hist = database.get_historian()
    return hist.archive.meta_get(obj_id)


def update_meta(*obj_or_identifier, meta: dict):
    """Update the metadata for a bunch of objects"""
    hist = database.get_historian()
    for obj_id in obj_or_identifier:
        hist.meta.update(obj_id, meta)


def set_meta(*obj_or_identifier, meta: dict):
    """Set the metadata for a bunch of objects"""
    hist = database.get_historian()
    obj_ids = tuple(map(to_obj_id, obj_or_identifier))

    # Preserve the internal keys
    for obj_id in obj_ids:
        hist.meta.set(obj_id, meta)


def find_meta(filter: dict = None, obj_ids=None):  # pylint: disable=redefined-builtin
    filter = filter or {}
    hist = database.get_historian()
    return hist.meta.find(filter, obj_ids)


# endregion

# region paths

PathInfo = collections.namedtuple('PathInfo', 'obj_id path')


def get_path(obj_or_id) -> Optional[str]:
    """Given an object or object id get the current path"""
    return get_paths(obj_or_id)[0].path


def get_paths(*obj_or_id, historian: mincepy.Historian = None) -> Sequence[PathInfo]:
    """Given objects or identifier this will return their current paths as PathInfo tuples in the order that they were
    passed in.  A PathInfo consists of the object id and the corresponding path.

    This choice of return value makes it easy to construct dictionaries, e.g.:
    >>> obj_paths = dict(get_path('obj123', 'obj456'))
    where object ids have been passed in as strings.  It is important to note, that when constructing such a dictionary
    duplicate values will be joined.  Whether this is desired will depend on the use case.
    """
    hist = historian or database.get_historian()
    obj_ids = tuple(map(hist.to_obj_id, obj_or_id))

    paths = []
    for obj_id, path in zip(obj_ids, fs.get_paths(*obj_ids, historian=historian)):
        paths.append(PathInfo(obj_id, os.withdb.from_fs_path(path)))

    return paths


def set_path(obj_id, path: os.PathSpec) -> str:
    """Given an object or object id set the current path and return the new abspath"""
    return set_paths((obj_id, path))[0].path


def set_paths(*obj_id_path: Tuple[Any, os.PathSpec],
              historian: mincepy.Historian = None) -> Sequence[PathInfo]:
    """Set the path for one or more objects.  This function expects (object or identifier, path) tuples and returns
    the corresponding PathInfo objects with absolute paths in the same order as the arguments"""
    hist = historian or database.get_historian()
    paths = []

    for obj_or_id, path in obj_id_path:
        obj_id = hist.to_obj_id(obj_or_id)

        fs.set_obj_path(obj_id, os.withdb.to_fs_path(path), historian=historian)

        paths.append(PathInfo(obj_id, os.path.abspath(path)))

    return paths


def rename(obj_or_id, dest: os.PathSpec):
    """Rename an object to the dest.  If dest is a directory IsADirectoryError is raised."""
    dest = os.fspath(dest)
    if dest.endswith(os.sep):
        raise exceptions.IsADirectoryError(dest)

    hist = database.get_historian()
    obj_id = hist.to_obj_id(obj_or_id)

    fs.rename(src_id=obj_id, dest=os.withdb.to_fs_path(dest), historian=hist)  # DB HIT


def get_abspath(obj_id, _meta: dict) -> str:
    """Given an object id this method will return a string representing
    the absolute path of the object"""
    assert obj_id, 'Must provide a valid obj id'
    return os.sep.join(fs.get_paths(obj_id)[0])


def homedir(user: str = '') -> str:
    """Return the user's home directory"""
    if not user:
        user_info = database.get_historian().get_user_info()
        user_name = user_info[mincepy.ExtraKeys.USER]
    else:
        user_name = user
    return f'/{user_name}'


# endregion


def save_one(obj,
             path: os.PathSpec = None,
             overwrite=False,
             meta=None,
             historian: mincepy.Historian = None):
    """Save one object at the given path.  The path can be a filename or a directory or a filename
    in a directory

    :param obj: the object to save
    :param path: the optional path to save it to
    :param overwrite: overwrite if there is already an object at that path
    :param meta: an optional dictionary of metadata to store with the object
    :param historian: the historian to use for saving
    """
    hist = historian or database.get_historian()
    obj_id = save_many(((obj, path),), overwrite=overwrite, show_progress=False, historian=hist)[0]
    if meta:
        hist.meta.set(obj_id, meta)

    return obj_id


def save_many(to_save: Iterable[Union[Any, Tuple[Any, os.PathSpec]]],
              overwrite=False,
              show_progress=True,
              historian: mincepy.Historian = None):
    """
    Save many objects, expects an iterable where each entry is an object to save or a tuple of
    length 2 containing the object and a path of where to save it.

    :param to_save: the iterable able objects to save
    :param overwrite: overwrite objects with the same name
    :param historian: the historian to use
    """

    def _parse_entry(entry):
        if isinstance(entry, tuple):
            return entry[0], entry[1]

        # Assume it's just the object
        return entry, None

    for entry in to_save:
        if isinstance(entry, tuple) and len(entry) > 2:
            raise ValueError('Can only pass sequences of at most length 2')

    obj_ids = []
    historian = historian or database.get_historian()

    progress_opts = dict(desc='Saving', disable=not show_progress)
    try:
        progress_opts['total'] = len(to_save)
    except TypeError:
        pass
    progress_bar = tqdm(**progress_opts)

    cache = fs.EntriesCache(historian)
    exc = None
    with historian.transaction():
        for entry in to_save:
            obj, path = _parse_entry(entry)

            # Set the object to be saved at the end of the transaction
            obj_id = historian.save_one(obj)
            if path is not None:
                # Get information about the source
                source_entry = cache.get_entry_from_id(obj_id)
                if source_entry is not None and fs.Entry.is_dir(source_entry):
                    raise exceptions.IsADirectoryError(path)

                # Get information about the destination
                save_path = os.withdb.to_fs_path(path)
                dest_entry = cache.get_entry_from_path(save_path)

                if dest_entry is not None and fs.Entry.is_dir(dest_entry):
                    if source_entry is None:
                        save_path = save_path + (str(obj_id),)
                    else:
                        save_path = save_path + (fs.Entry.name(source_entry),)

                if source_entry is None:
                    _insert(obj_id, save_path, overwrite=overwrite, cache=cache)
                else:
                    _rename(obj_id, save_path, overwrite=overwrite, cache=cache)

            obj_ids.append(obj_id)
            progress_bar.update(1)

    if exc is not None:
        raise exc  # pylint: disable=raising-bad-type

    return obj_ids


def load(*identifier):
    """Load one or more objects"""
    database.get_historian().load(*identifier)


def to_obj_id(identifier):
    """Get the database object id from the passed identifier.  If the identifier is already a
    mincePy object id it will be returned unaltered.  Otherwise, mincePy will try and turn the type
    into an object id.  If it fails, None is returned"""
    return database.get_historian().to_obj_id(identifier)


@deprecation.deprecated(deprecated_in='0.7.10',
                        removed_in='0.8.0',
                        current_version=version.__version__,
                        details='Use next(get_obj_id_from_path()) instead')
def get_obj_id(path: os.PathSpec):
    """Given a path get the id of the corresponding object.  Returns None if not found."""
    return next(get_obj_id_from_path(path))


def get_obj_id_from_path(*path: os.PathSpec) -> Iterator:
    """Given a path yield the id of the corresponding object.  Yields None if not found."""
    for entry in path:
        entry = os.fspath(entry)

        # Check if the basename is an object id
        basename = os.path.basename(entry)
        if basename:
            hist = database.get_historian()
            try:
                yield hist.archive.construct_archive_id(basename)
                continue
            except ValueError:
                pass

        entry = fs.find_entry(os.withdb.to_fs_path(entry))
        if entry is None:
            yield None
        else:
            yield fs.Entry.id(entry)


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
    hist = database.get_historian()

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


def _insert(obj_id,
            dest: fs.Path,
            overwrite=False,
            historian: mincepy.Historian = None,
            cache: fs.EntriesCache = None):
    cache = cache or fs.EntriesCache(historian)
    historian = cache.historian

    try:
        fs.insert_obj(obj_id, dest, cache=cache)  # DB HIT
    except exceptions.FileExistsError:
        if overwrite:
            conflicting_id = fs.Entry.id(cache.get_entry_from_path(dest))
            historian.delete(conflicting_id)
            fs.remove_obj(conflicting_id, historian=historian)  # DB HIT

            # Try again
            fs.insert_obj(obj_id, dest, cache=cache)  # DB HIT
        else:
            raise


def _rename(obj_id,
            dest: fs.Path,
            overwrite=False,
            historian: mincepy.Historian = None,
            cache: fs.EntriesCache = None):
    cache = cache or fs.EntriesCache(historian)
    historian = cache.historian

    try:
        fs.rename(src_id=obj_id, dest=dest, cache=cache)  # DB HIT
    except exceptions.FileExistsError:
        if overwrite:
            conflicting_id = fs.Entry.id(cache.get_entry_from_path(dest))  # DB HIT
            historian.delete(conflicting_id)
            fs.remove_obj(conflicting_id, historian=historian)  # DB HIT

            # Try again
            fs.rename(src_id=obj_id, dest=dest, cache=cache)  # DB_HIT
        else:
            raise
