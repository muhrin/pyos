# -*- coding: utf-8 -*-
"""Methods and classes that can require interaction with the db module and therefore cannot be used by db itself."""
import pathlib
from typing import List, Iterator

import mincepy

from pyos import db
from pyos.db import fs
from pyos import exceptions
from . import nodb
from . import types

from .nodb import sep, curdir, pardir


def isdir(path: types.PathSpec) -> bool:
    """Return True if path is an existing directory."""
    entry = fs.find_entry(to_fs_path(path))
    if not entry:
        return False
    return fs.Entry.is_dir(entry)


def isfile(path: types.PathSpec) -> bool:
    entry = fs.find_entry(to_fs_path(path))
    if not entry:
        return False
    return fs.Entry.is_obj(entry)


def exists(path: types.PathSpec) -> bool:
    """Return `True` if the path exists"""
    return db.fs.find_entry(to_fs_path(path)) is not None


# Don't support links for now, so fall back to exists
lexists = exists


def abspath(path: types.PathSpec) -> str:
    """Return a normalised absolutised version of the pathname path. This is equivalent to calling
    the function normpath() as follows: normpath(join(os.getcwd(), path)).
    """
    path = nodb.fspath(path)
    if nodb.isabs(path):
        return path

    return nodb.normpath(nodb.join(getcwd(), path))


def relpath(path: types.PathSpec, start=curdir) -> str:
    """
    Return a relative filepath to path either from the current directory or from an optional start
    directory. This is a path computation: the filesystem is not accessed to confirm the existence
    or nature of path or start.

    start defaults to curdir.

    :param path: the path to get the relative path for
    :param start: the start directory
    """
    if not path:
        raise ValueError('no path specified')

    path = nodb.fspath(path)

    if start is None:
        start = curdir
    else:
        start = nodb.fspath(start)

    try:
        start_list = [x for x in abspath(start).split(sep) if x]
        path_list = [x for x in abspath(path).split(sep) if x]
        # Work out how much of the filepath is shared by start and path.
        i = len(nodb.commonprefix([start_list, path_list]))

        rel_list = [pardir] * (len(start_list) - i) + path_list[i:]
        if not rel_list:
            return curdir

        return nodb.join(*rel_list)
    except (TypeError, AttributeError, DeprecationWarning):
        nodb.check_arg_types('relpath', path, start)
        raise


def expanduser(path: types.PathSpec) -> str:
    """An initial `~` is replaced with the users home directory which is '/[username]'/."""
    tilde = '~'
    path = nodb.fspath(path)
    if not path.startswith(tilde):
        return path

    i = path.find(sep, 1)
    if i < 0:
        i = len(path)

    homedir = db.homedir(path[1:i])
    return homedir + path[i + 1:]  # Have to add one to get past the trailing '/'


# region pyos.os


def chdir(path: types.PathSpec):
    """
    Change the current working directory to path.

    :param path: the path to change to
    """
    path = abspath(path)
    if not path.endswith(sep):
        path += sep
    if not exists(path):
        raise exceptions.FileNotFoundError(f'No such file or directory {path}')
    if not isdir(path):
        raise exceptions.NotADirectoryError(f'Not a directory {path}')

    db.get_session().set_cwd(to_fs_path(path))


def getcwd() -> str:
    """Return a string representing the current working directory."""
    return from_fs_path(db.get_session().cwd)


def listdir(lsdir: types.PathSpec = '.') -> List[str]:
    entry = db.fs.find_entry(to_fs_path(lsdir))  # DB HIT
    if not entry:
        raise exceptions.FileNotFoundError(lsdir)

    if db.fs.Entry.is_obj(entry):
        raise exceptions.NotADirectoryError(f"Not a directory: '{lsdir}'")

    return [db.fs.Entry.name(child) for child in fs.iter_children(fs.Entry.id(entry))]


def open(
        # pylint: disable=redefined-builtin
        file: types.PathSpec,
        mode='r',
        encoding: str = None) -> mincepy.File:
    """
    Open file and return a corresponding file object.

    :param file: the path-like object that gives the pathname to open
    :param mode: the opening mode
    :param encoding: the encoding to use
    :return: a file-like object that can be used to interact with the file
    """
    file_path = abspath(file)
    entry = db.fs.find_entry(file_path)

    if entry is None:
        # Create a new one
        fileobj = db.get_historian().create_file(file_path, encoding=encoding)
        db.save_one(fileobj, file_path)
    else:
        if fs.Entry.is_dir(entry):
            raise exceptions.IsADirectoryError(file_path)

        fileobj = db.load(fs.Entry.id(entry))
        if not isinstance(file, mincepy.File):
            raise ValueError(f'open: {fileobj}: is not a file')

    # if file_path.endswith(sep):
    #     raise exceptions.IsADirectoryError(file_path)
    #
    # results = db.find_meta(db.path_to_meta_dict(file_path))
    # try:
    #     obj_id = next(results)['obj_id']
    #     fileobj = db.load(obj_id)
    #     if not isinstance(file, mincepy.File):
    #         raise ValueError(f'open: {fileobj}: is not a file')
    # except StopIteration:
    #     # Create a new one
    #     fileobj = db.get_historian().create_file(file_path, encoding=encoding)
    #     db.save_one(fileobj, file_path)

    return fileobj.open(mode=mode)


def rename(src: types.PathSpec, dest: types.PathSpec):
    """Rename the file or directory src to dest.
    If src is a file and dest is a directory or vice-versa, an IsADirectoryError or a
    NotADirectoryError will be raised respectively.
    If both are directories and dest is not empty, an PyOSError is raised.
    If both are files, dst it will be replaced silently.
    """
    src = nodb.fspath(src)
    dest = nodb.fspath(dest)

    try:
        db.fs.rename(to_fs_path(src), to_fs_path(dest))
    except exceptions.FileExistsError as exc:
        # Reraise using the original `dest`
        raise exceptions.FileExistsError(dest) from exc


def remove(file_path: types.PathSpec):
    """Remove (delete) the file path. If path is a directory, an IsADirectoryError is raised. Use
    rmdir() to remove directories."""
    file_path = abspath(file_path)
    if file_path.endswith(sep):
        raise exceptions.IsADirectoryError(file_path)

    obj_id = next(db.get_obj_id_from_path(file_path))
    db.get_historian().delete(obj_id)
    db.fs.remove_obj(obj_id)


class _ScandirIter:

    def __init__(self, iterator: Iterator):
        self._iterator = iterator

    def __iter__(self):
        return self._iterator

    def __next__(self):
        return self._iterator.__next__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Nothing to do"""

    def close(self):
        """Close does nothing here"""


def scandir(scan_path='.') -> Iterator[nodb.DirEntry]:
    entry = db.fs.find_entry(to_fs_path(scan_path))
    if not entry:
        raise exceptions.FileNotFoundError(scan_path)

    if db.fs.Entry.is_obj(entry):
        raise exceptions.NotADirectoryError(f"Not a directory: '{scan_path}'")

    contents = []
    for descendent in db.fs.iter_children(db.fs.Entry.id(entry)):
        obj_name = db.fs.Entry.name(descendent)
        contents.append(
            nodb.DirEntry(obj_name=obj_name,
                          obj_path=nodb.join(scan_path, obj_name),
                          is_file=fs.Entry.is_obj(descendent)))

    return _ScandirIter(iter(contents))


def unlink(file_path: types.PathSpec):
    """
    Remove (delete) the file path. This function is semantically identical to remove(); the unlink
    name is its traditional Unix name. Please see the documentation for remove() for further
    information.

    :param file_path: the path to remove
    """
    return remove(file_path)


def makedirs(name: types.PathSpec, exists_ok=False):
    try:
        db.fs.make_dirs(to_fs_path(name), exists_ok=exists_ok)
    except exceptions.FileExistsError as exc:
        # Reraise using the passed name
        raise exceptions.FileExistsError(name) from exc


# endregion


def to_fs_path(path: types.PathSpec) -> db.fs.Path:
    parts = pathlib.PosixPath(abspath(path)).parts
    db.fs.validate_path(parts)
    return parts


def from_fs_path(fs_path: db.fs.Path) -> str:
    db.fs.validate_path(fs_path)
    return str(pathlib.PosixPath(*fs_path))
