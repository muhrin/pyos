"""Functions and constants that emulate python's os module"""
import mincepy

__all__ = 'getcwd', 'chdir', 'fspath', 'remove', 'sep', 'unlink', 'curdir', 'pardir'

import pyos
from . import types

# pylint: disable=invalid-name
name = 'pyos'
sep = '/'  # The path separator pylint: disable=invalid-name
# Used to refer to the current directory
curdir = '.'
# Used to refer to the parent directory
pardir = '..'


def chdir(path: types.PathSpec):
    """
    Change the current working directory to path.

    :param path: the path to change to
    """
    path = pyos.os.path.abspath(path)
    if not path.endswith(sep):
        raise ValueError("Must supply a directory, got '{}'".format(path))
    pyos.db.get_historian().meta.sticky[pyos.config.DIR_KEY] = path


def fspath(path: types.PathSpec):
    """Return the pyos representation of the path.

    If str is passed in, it is returned unchanged.
    Otherwise __fspath__() is called and its value is returned as long as it is a str. In all other
    cases, TypeError is raised."""
    if isinstance(path, str):
        return path

    # Work from the object's type to match method resolution of other magic methods.
    path_type = type(path)
    try:
        path_repr = path_type.__fspath__(path)
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
    return pyos.db.get_historian().meta.sticky.get(pyos.config.DIR_KEY, None)


# pylint: disable=redefined-builtin
def open(file: types.PathSpec, mode='r', encoding: str = None) -> mincepy.File:
    """
    Open file and return a corresponding file object.

    :param file: the path-like object that gives the pathname to open
    :param mode: the opening mode
    :param encoding: the encoding to use
    :return: a file-like object that can be used to interact with the file
    """
    path = pyos.os.path.abspath(file)
    if path.endswith(sep):
        raise pyos.IsADirectoryError(file)

    results = pyos.db.find_meta(pyos.db.path_to_meta_dict(path))
    try:
        obj_id = next(results)['obj_id']
        fileobj = pyos.db.load(obj_id)
        if not isinstance(file, mincepy.File):
            raise ValueError("open: {}: is not a file".format(fileobj))
    except StopIteration:
        # Create a new one
        fileobj = pyos.db.get_historian().create_file(path, encoding=encoding)
        pyos.db.save_one(fileobj, path)

    return fileobj.open(mode=mode)


def remove(path: types.PathSpec):
    """Remove (delete) the file path. If path is a directory, an IsADirectoryError is raised. Use
    rmdir() to remove directories."""
    path = pyos.os.path.abspath(path)
    if path.endswith(sep):
        raise pyos.IsADirectoryError(path)

    obj_id = pyos.db.get_obj_id(path)
    pyos.db.get_historian().delete(obj_id)


def unlink(path: types.PathSpec):
    """
    Remove (delete) the file path. This function is semantically identical to remove(); the unlink
    name is its traditional Unix name. Please see the documentation for remove() for further
    information.

    :param path: the path to remove
    """
    return remove(path)
