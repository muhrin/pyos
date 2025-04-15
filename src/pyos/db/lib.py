import collections
from typing import TYPE_CHECKING, Any, Iterable, Iterator, Optional, Sequence, Union

import deprecation
import mincepy
from tqdm import tqdm

from . import fs
from .. import _globals, exceptions, os, version

if TYPE_CHECKING:
    import pyos

__all__ = (
    "get_meta",
    "update_meta",
    "set_meta",
    "find_meta",
    "save_one",
    "save_many",
    "get_abspath",
    "load",
    "to_obj_id",
    "get_obj_id",
    "get_path",
    "get_paths",
    "rename",
    "homedir",
    "get_oid",
    "get_obj_id_from_path",
    "set_path",
    "set_paths",
)


# region metadata


def get_meta(obj_id: Union[Any, Iterable[Any]], session: Optional["pyos.Session"] = None):
    """Get the metadata for a bunch of objects"""
    session = session if session is not None else _globals.get_global_session()
    return session.historian.archive.meta_get(obj_id)


def update_meta(*obj_or_identifier, meta: dict, session: Optional["pyos.Session"] = None):
    """Update the metadata for a bunch of objects"""
    session = session if session is not None else _globals.get_global_session()
    for obj_id in obj_or_identifier:
        session.historian.meta.update(obj_id, meta)


def set_meta(*obj_or_identifier, meta: dict, session: Optional["pyos.Session"] = None):
    """Set the metadata for a bunch of objects"""
    session = session if session is not None else _globals.get_global_session()
    obj_ids = tuple(map(to_obj_id, obj_or_identifier))

    # Preserve the internal keys
    for obj_id in obj_ids:
        session.historian.meta.set(obj_id, meta)


def find_meta(
    filter: dict = None, obj_ids=None, session: Optional["pyos.Session"] = None
):  # pylint: disable=redefined-builtin
    session = session if session is not None else _globals.get_global_session()
    filter = filter or {}
    return session.historian.meta.find(filter, obj_ids)


# endregion

# region paths

PathInfo = collections.namedtuple("PathInfo", "obj_id path")


def get_path(obj_or_id) -> Optional[str]:
    """Given an object or object id get the current path"""
    return get_paths(obj_or_id)[0].path


def get_paths(*obj_or_id, session: Optional["pyos.Session"] = None) -> Sequence[PathInfo]:
    """Given objects or identifier this will return their current paths as PathInfo tuples in the
    order that they were passed in.  A PathInfo consists of the object id and the corresponding
    path.

    This choice of return value makes it easy to construct dictionaries, e.g.:
    >>> obj_paths = dict(get_path('obj123', 'obj456'))
    where object ids have been passed in as strings.  It is important to note, that when
    constructing such a dictionary duplicate values will be joined.  Whether this is desired will
    depend on the use case.
    """
    session = session if session is not None else _globals.get_global_session()

    obj_ids = tuple(map(session.historian.to_obj_id, obj_or_id))

    paths = []
    for obj_id, path in zip(obj_ids, fs.get_paths(*obj_ids, session=session)):
        paths.append(PathInfo(obj_id, os.withdb.from_fs_path(path)))

    return paths


def set_path(obj_id, path: "pyos.os.PathSpec") -> str:
    """Given an object or object id set the current path and return the new abspath"""
    return set_paths((obj_id, path))[0].path


def set_paths(
    *obj_id_path: tuple[Any, "pyos.os.PathSpec"], session: Optional["pyos.Session"] = None
) -> Sequence[PathInfo]:
    """Set the path for one or more objects.  This function expects (object or identifier, path)
    tuples and returns the corresponding PathInfo objects with absolute paths in the same order
    as the arguments
    """
    session = session if session is not None else _globals.get_global_session()
    paths = []

    for obj_or_id, path in obj_id_path:
        obj_id = session.historian.to_obj_id(obj_or_id)

        fs.set_obj_path(obj_id, os.withdb.to_fs_path(path), session=session)

        paths.append(PathInfo(obj_id, os.path.abspath(path)))

    return paths


def rename(obj_or_id, dest: "pyos.os.PathSpec", session: Optional["pyos.Session"] = None):
    """Rename an object to the dest.  If dest is a directory IsADirectoryError is raised."""
    dest = os.fspath(dest)
    if dest.endswith(os.sep):
        raise exceptions.IsADirectoryError(dest)

    session = session if session is not None else _globals.get_global_session()
    obj_id = session.historian.to_obj_id(obj_or_id)

    fs.rename(src_id=obj_id, dest=os.withdb.to_fs_path(dest), session=session)  # DB HIT


def get_abspath(obj_id, _meta: dict) -> str:
    """Given an object id this method will return a string representing
    the absolute path of the object"""
    assert obj_id, "Must provide a valid obj id"
    return os.sep.join(fs.get_paths(obj_id)[0])


def homedir(user: str = "", session: Optional["pyos.Session"] = None) -> str:
    """Return the user's home directory"""
    session = session if session is not None else _globals.get_global_session()

    if not user:
        user_info = session.historian.get_user_info()
        user_name = user_info[mincepy.ExtraKeys.USER]
    else:
        user_name = user
    return f"/{user_name}"


# endregion


def save_one(
    obj,
    path: os.PathSpec = None,
    overwrite=False,
    meta: dict = None,
    session: Optional["pyos.Session"] = None,
):
    """Save one object at the given path.  The path can be a filename or a directory or a filename
    in a directory

    :param obj: the object to save
    :param path: the optional path to save it to
    :param overwrite: overwrite if there is already an object at that path
    :param meta: an optional dictionary of metadata to store with the object
    :param historian: the historian to use for saving
    """
    obj_id = save_many(((obj, path),), overwrite=overwrite, show_progress=False, session=session)[0]
    if meta:
        session = session if session is not None else _globals.get_global_session()
        session.historian.meta.set(obj_id, meta)

    return obj_id


def save_many(
    to_save: Iterable[Union[Any, tuple[Any, os.PathSpec]]],
    overwrite=False,
    show_progress=True,
    session: Optional["pyos.Session"] = None,
):
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
            raise ValueError("Can only pass sequences of at most length 2")

    obj_ids = []
    session = session if session is not None else _globals.get_global_session()

    progress_opts = dict(desc="Saving", disable=not show_progress)
    try:
        progress_opts["total"] = len(to_save)
    except TypeError:
        pass
    progress_bar = tqdm(**progress_opts)

    cache = fs.EntriesCache(session)
    exc = None
    with cache.historian.transaction():
        for entry in to_save:
            obj, path = _parse_entry(entry)

            # Set the object to be saved at the end of the transaction
            obj_id = cache.historian.save_one(obj)
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


def load(*identifier, session: Optional["pyos.Session"] = None):
    """Load one or more objects"""
    session = session if session is not None else _globals.get_global_session()
    session.historian.load(*identifier)


def to_obj_id(identifier, session: Optional["pyos.Session"] = None):
    """
    Get the database object id from the passed identifier.  If the identifier is already a
    mincePy object id it will be returned unaltered.  Otherwise, mincePy will try and turn the type
    into an object id.  If it fails, `None` is returned
    """
    session = session if session is not None else _globals.get_global_session()
    return session.historian.to_obj_id(identifier)


@deprecation.deprecated(
    deprecated_in="0.7.10",
    removed_in="0.8.0",
    current_version=version.__version__,
    details="Use next(get_obj_id_from_path()) instead",
)
def get_obj_id(path: os.PathSpec):
    """Given a path get the id of the corresponding object.  Returns None if not found."""
    return next(get_obj_id_from_path(path))


def get_obj_id_from_path(*path: os.PathSpec, session: Optional["pyos.Session"] = None) -> Iterator:
    """Given a path yield the id of the corresponding object.  Yields None if not found."""
    session = session if session is not None else _globals.get_global_session()

    for entry in path:
        entry = os.fspath(entry)

        # Check if the basename is an object id
        basename = os.path.basename(entry)
        if basename:
            try:
                yield session.historian.archive.construct_archive_id(basename)
                continue
            except ValueError:
                pass

        entry = fs.find_entry(os.withdb.to_fs_path(entry), session=session)
        if entry is None:
            yield None
        else:
            yield fs.Entry.id(entry)


def get_oid(*identifier, session: Optional["pyos.Session"] = None) -> Iterator:
    """Get one or more object ids.

    :param identifier: can be any of the following:
        * an object id
        * an object instance
        * a string representing a valid object id
        * the path to an object
        these will be tested in order in an attempt to get the object id.  If all fail then None
        will be yielded.
    """
    session = session if session is not None else _globals.get_global_session()

    for ident in identifier:
        obj_id = None

        if ident is not None:
            # Let the historian try to interpret it, no db access
            obj_id = session.historian.to_obj_id(ident)

            if obj_id is None:
                # Maybe it is a path
                try:
                    path = os.fspath(ident)
                except TypeError:
                    pass
                else:
                    obj_id = next(  # pylint: disable=stop-iteration-return
                        get_obj_id_from_path(path)
                    )

        yield obj_id


def _insert(
    obj_id,
    dest: fs.Path,
    overwrite=False,
    session: Optional["pyos.Session"] = None,
    cache: fs.EntriesCache = None,
):
    cache = cache or fs.EntriesCache(session)
    historian = cache.historian

    try:
        fs.insert_obj(obj_id, dest, cache=cache)  # DB HIT
    except exceptions.FileExistsError:
        if overwrite:
            conflicting_id = fs.Entry.id(cache.get_entry_from_path(dest))
            historian.delete(conflicting_id)
            fs.remove_obj(conflicting_id, session=cache.session)  # DB HIT

            # Try again
            fs.insert_obj(obj_id, dest, cache=cache)  # DB HIT
        else:
            raise


def _rename(
    obj_id,
    dest: fs.Path,
    overwrite=False,
    session: Optional["pyos.Session"] = None,
    cache: fs.EntriesCache = None,
):
    cache = cache or fs.EntriesCache(session)
    historian = cache.historian

    try:
        fs.rename(src_id=obj_id, dest=dest, cache=cache)  # DB HIT
    except exceptions.FileExistsError:
        if overwrite:
            conflicting_id = fs.Entry.id(cache.get_entry_from_path(dest))  # DB HIT
            historian.delete(conflicting_id)
            fs.remove_obj(conflicting_id, session=cache.session)  # DB HIT

            # Try again
            fs.rename(src_id=obj_id, dest=dest, cache=cache)  # DB_HIT
        else:
            raise
