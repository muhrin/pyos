"""Pyos versions os python's os.path methods"""
import posixpath
from typing import Iterable

import pyos
from . import types
from . import pos

from .pos import curdir, sep, pardir


def isabs(path: types.PathSpec):
    """Test whether a path is absolute

    :type path: pyos.os.PathSpec
    """
    return pos.fspath(path).startswith(pos.sep)


def abspath(path: types.PathSpec) -> str:
    """Return a normalised absolutised version of the pathname path. This is equivalent to calling
    the function normpath() as follows: normpath(join(os.getcwd(), path)).
    """
    path = pos.fspath(path)
    if isabs(path):
        return path

    return normpath(join(pos.getcwd(), path))


def join(path: types.PathSpec, *paths: Iterable[types.PathSpec]) -> str:
    """Join one or more path components intelligently. The return value is the concatenation of path
    and any members of *paths with exactly one directory separator (os.sep) following each non-empty
    part except the last, meaning that the result will only end in a separator if the last part is
    empty. If a component is an absolute path, all previous components are thrown away and joining
    continues from the absolute path component.
    """
    return posixpath.join(pos.fspath(path), *[pos.fspath(entry) for entry in paths])


def normpath(path: types.PathSpec) -> str:
    """Normalise a pathname by collapsing redundant separators and up-level references so that A//B,
    A/./B and A/foo/../B all become A/B.  The standard pyos distinction between object paths and
    directories is maintained to paths ending with a '/' will be kept as such.

    :type path: pyos.os.PathSpec
    """
    dot = '.'
    path = pos.fspath(path)
    final_slash = path.endswith(sep)
    path = posixpath.normpath(path)
    if path.startswith('//'):
        path = path[1:]
    if (final_slash or path == dot) and path != '/':
        path += sep

    return path or dot + sep


def basename(path: types.PathSpec) -> str:
    """Return the base name of pathname path. This is the second element of the pair returned by
    passing path to the function split(). Note that the result of this function is different from
    the Unix basename program; where basename for '/foo/bar/' returns 'bar', the basename() function
    returns an empty string ('').
    """
    return posixpath.basename(pos.fspath(path))


def dirname(path: types.PathSpec) -> str:
    """Return the directory name of pathname path. This is the first element of the pair returned by
    passing path to the function split()."""
    return posixpath.basename(pos.fspath(path))


def exists(path: types.PathSpec):
    """Return `True` if the path exists"""
    path = pyos.os.path.abspath(path)
    query = pyos.db.path_to_meta_dict(path)
    if path.endswith(sep):
        query[pyos.config.DIR_KEY] = {'$regex': '{}.*'.format(query[pyos.config.DIR_KEY])}

    results = pyos.db.find_meta(query)
    try:
        # Check if we have hits
        next(results)
        return True
    except StopIteration:
        return False


def split(path: types.PathSpec) -> tuple:
    """Split the pathname path into a pair, (head, tail) where tail is the last pathname component
    and head is everything leading up to that. The tail part will never contain a slash; if path
    ends in a slash, tail will be empty. If there is no slash in path, head will be empty. If path
    is empty, both head and tail are empty.
    In all cases, join(head, tail) returns a path to the same location as path (but the strings may
    differ).
    """
    parts = posixpath.split(pos.fspath(path))
    if parts[0]:
        parts = (parts[0] + pos.sep, parts[1])
    return parts


def relpath(path: types.PathSpec, start=pos.curdir) -> str:
    """
    Return a relative filepath to path either from the current directory or from an optional start
    directory. This is a path computation: the filesystem is not accessed to confirm the existence
    or nature of path or start.

    start defaults to pos.curdir.

    :param path: the path to get the relative path for
    :param start: the start directory
    """
    if not path:
        raise ValueError("no path specified")

    path = pos.fspath(path)

    if start is None:
        start = curdir
    else:
        start = pos.fspath(start)

    try:
        start_list = [x for x in abspath(start).split(sep) if x]
        path_list = [x for x in abspath(path).split(sep) if x]
        # Work out how much of the filepath is shared by start and path.
        i = len(commonprefix([start_list, path_list]))

        rel_list = [pardir] * (len(start_list) - i) + path_list[i:]
        if not rel_list:
            return curdir
        return join(*rel_list)
    except (TypeError, AttributeError, DeprecationWarning):
        _check_arg_types('relpath', path, start)
        raise


# Return the longest prefix of all list elements.
def commonprefix(names):
    """Given a list of pathnames, returns the longest common leading component"""
    if not names:
        return ''
    if not isinstance(names[0], (list, tuple)):
        names = tuple(map(pos.fspath, names))
    str1 = min(names)
    str2 = max(names)
    for i, char in enumerate(str1):
        if char != str2[i]:
            return str1[:i]
    return str1


def _check_arg_types(funcname, *args):
    for arg in args:
        if not isinstance(arg, str):
            raise TypeError('{}() argument must be str, bytes, or '
                            'os.PathLike object, not {}'.format(funcname,
                                                                arg.__class__.__name__)) from None
