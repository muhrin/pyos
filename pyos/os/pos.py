"""Functions and constants that emulate python's os module"""
import mincepy

from pyos import config
from pyos import db
from pyos import exceptions
from . import path
from . import types

from .path import (curdir, pardir, sep)

# pylint: disable=invalid-name
name = 'pyos'

__all__ = ('getcwd', 'chdir', 'fspath', 'remove', 'sep', 'unlink', 'curdir', 'pardir', 'path',
           'rename')


def chdir(file_path: types.PathSpec):
    """
    Change the current working directory to path.

    :param file_path: the path to change to
    """
    file_path = path.abspath(file_path)
    if not file_path.endswith(sep):
        raise ValueError("Must supply a directory, got '{}'".format(file_path))
    db.get_historian().meta.sticky[config.DIR_KEY] = file_path


def fspath(file_path: types.PathSpec):
    """Return the pyos representation of the path.

    If str is passed in, it is returned unchanged.
    Otherwise __fspath__() is called and its value is returned as long as it is a str. In all other
    cases, TypeError is raised."""
    if isinstance(file_path, str):
        return file_path

    # Work from the object's type to match method resolution of other magic methods.
    path_type = type(file_path)
    try:
        path_repr = path_type.__fspath__(file_path)
    except AttributeError:
        if hasattr(path_type, '__fspath__'):
            raise

        raise TypeError("expected str or os.PathLike object, not " + path_type.__name__)

    if isinstance(path_repr, str):
        return path_repr

    raise TypeError("expected {}.__fspath__() to return str, not {}".format(
        path_type.__name__,
        type(path_repr).__name__))


def getcwd() -> str:
    """Return a string representing the current working directory."""
    return db.get_historian().meta.sticky.get(config.DIR_KEY, None)


# pylint: disable=redefined-builtin
def open(file: types.PathSpec, mode='r', encoding: str = None) -> mincepy.File:
    """
    Open file and return a corresponding file object.

    :param file: the path-like object that gives the pathname to open
    :param mode: the opening mode
    :param encoding: the encoding to use
    :return: a file-like object that can be used to interact with the file
    """
    file_path = path.abspath(file)
    if file_path.endswith(sep):
        raise exceptions.IsADirectoryError(file_path)

    results = db.find_meta(db.path_to_meta_dict(file_path))
    try:
        obj_id = next(results)['obj_id']
        fileobj = db.load(obj_id)
        if not isinstance(file, mincepy.File):
            raise ValueError("open: {}: is not a file".format(fileobj))
    except StopIteration:
        # Create a new one
        fileobj = db.get_historian().create_file(file_path, encoding=encoding)
        db.save_one(fileobj, file_path)

    return fileobj.open(mode=mode)


def remove(file_path: types.PathSpec):
    """Remove (delete) the file path. If path is a directory, an IsADirectoryError is raised. Use
    rmdir() to remove directories."""
    file_path = path.abspath(file_path)
    if file_path.endswith(sep):
        raise exceptions.IsADirectoryError(file_path)

    obj_id = db.get_obj_id(file_path)
    db.get_historian().delete(obj_id)


def rename(src: types.PathSpec, dest: types.PathSpec):
    """Rename the file or directory src to dest.
    If src is a file and dest is a directory or vice-versa, an IsADirectoryError or a
    NotADirectoryError will be raised respectively.
    If both are directories and dest is not empty, an OSError is raised.
    If both are files, dst it will be replaced silently.
    """
    src = fspath(src)
    dest = fspath(dest)
    if src.endswith(sep):
        # Renaming directory
        if not dest.endswith(sep):
            raise exceptions.NotADirectoryError(dest)

        if path.exists(dest):
            # In pyOS a directory must have something in it to exist
            raise OSError("The destination directory '{}' is not empty.".format(dest))

        historian = db.get_historian()
        with historian.transaction():
            # Find everything within this folder at any depth
            query = db.queries.subdirs(src, start_depth=0, end_depth=-1)
            len_src = len(src)
            for obj_id, meta in historian.meta.find(query):
                current = meta[config.DIR_KEY]
                # Update the directory key to contain the new path
                meta[config.DIR_KEY] = path.join(dest, current[len_src:])
                historian.meta.set(obj_id, meta)
    else:
        # Renaming file
        if dest.endswith(sep):
            raise exceptions.IsADirectoryError(dest)

        historian = db.get_historian()
        try:
            obj_id, meta = next(historian.meta.find(db.utils.path_to_meta_dict(src)))
        except StopIteration:
            # Check if the source corresponds to an object id
            obj_id = historian.to_obj_id(path.basename(src))
            if obj_id is None:
                raise exceptions.FileNotFoundError(src)
            meta = historian.meta.get(obj_id)

        # Update the metadata
        meta.update(db.utils.path_to_meta_dict(dest))
        historian.meta.set(obj_id, meta=meta)


def unlink(file_path: types.PathSpec):
    """
    Remove (delete) the file path. This function is semantically identical to remove(); the unlink
    name is its traditional Unix name. Please see the documentation for remove() for further
    information.

    :param file_path: the path to remove
    """
    return remove(file_path)
