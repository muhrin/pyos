# -*- coding: utf-8 -*-
"""Methods and classes that do not need interaction with the database and are therefore safe to use from modules
that need access to pyos.db without causing a cyclic dependency."""
import posixpath
from typing import Union

from . import types

# pylint: disable=invalid-name

sep = '/'  # The path separator pylint: disable=invalid-name
curdir = '.'  # Used to refer to the current directory
pardir = '..'  # Used to refer to the parent directory

_ENCODING = 'UTF-8'

isabs = posixpath.isabs
join = posixpath.join
normpath = posixpath.normpath
basename = posixpath.basename
dirname = posixpath.dirname
split = posixpath.split
commonprefix = posixpath.commonprefix


def check_arg_types(funcname, *args):
    for arg in args:
        if not isinstance(arg, str):
            raise TypeError(f'{funcname}() argument must be str, bytes, or '
                            'os.PathLike object, not {arg.__class__.__name__}') from None


# region pyos.os


class DirEntry:

    def __init__(self, obj_name: str, obj_path: str, is_file: bool):
        self._name = obj_name
        self._path = obj_path
        self._is_file = is_file

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> str:
        return self._path

    def is_dir(self):
        return not self.is_file()

    def is_file(self):
        return self._is_file


def fspath(file_path: types.PathSpec) -> Union[str, bytes]:
    """Return the pyOS representation of the path.

    If str is passed in, it is returned unchanged.
    Otherwise, __fspath__() is called and its value is returned as long as it is a str. In all other
    cases, TypeError is raised."""
    if isinstance(file_path, (str, bytes)):
        return file_path

    # Work from the object's type to match method resolution of other magic methods.
    path_type = type(file_path)
    try:
        path_repr = path_type.__fspath__(file_path)  # pylint: disable=unnecessary-dunder-call
    except AttributeError:
        if hasattr(path_type, '__fspath__'):
            raise

        raise TypeError('expected str or os.PathLike object, not ' + path_type.__name__) from None

    if isinstance(path_repr, (str, bytes)):
        return path_repr

    raise TypeError(
        f'expected {path_type.__name__}.__fspath__() to return str, not {type(path_repr).__name__}')


def fsencode(filename: types.PathSpec) -> bytes:
    filename = fspath(filename)
    if isinstance(filename, str):
        return filename.encode(_ENCODING)
    # else:
    return filename


def fsdecode(filename: types.PathSpec) -> str:
    filename = fspath(filename)  # Does type-checking of `filename`.
    if isinstance(filename, bytes):
        return filename.decode(_ENCODING)
    # else:
    return filename


splitdrive = posixpath.splitdrive

# endregion
