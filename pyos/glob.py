# -*- coding: utf-8 -*-
"""Filename globbing utility."""

import contextlib
import re
import fnmatch
import itertools

from pyos import os
from pyos import exceptions

__all__ = ['glob', 'iglob', 'escape']


def glob(pathname, *, root_dir=None, recursive=False, include_hidden=False):
    """Return a list of paths matching a pathname pattern.

    The pattern may contain simple shell-style wildcards a la
    fnmatch. Unlike fnmatch, filenames starting with a
    dot are special cases that are not matched by '*' and '?'
    patterns by default.

    If `include_hidden` is true, the patterns '*', '?', '**'  will match hidden
    directories.

    If `recursive` is true, the pattern '**' will match any files and
    zero or more directories and subdirectories.
    """
    return list(
        iglob(pathname, root_dir=root_dir, recursive=recursive, include_hidden=include_hidden))


def iglob(pathname, *, root_dir=None, recursive=False, include_hidden=False):
    """Return an iterator which yields the paths matching a pathname pattern.

    The pattern may contain simple shell-style wildcards a la
    fnmatch. However, unlike fnmatch, filenames starting with a
    dot are special cases that are not matched by '*' and '?'
    patterns.

    If recursive is true, the pattern '**' will match any files and
    zero or more directories and subdirectories.
    """
    if root_dir is not None:
        root_dir = os.fspath(root_dir)
    else:
        root_dir = pathname[:0]
    itr = _iglob(pathname, root_dir, recursive, False, include_hidden=include_hidden)
    if not pathname or recursive and _isrecursive(pathname[:2]):
        try:
            string = next(itr)  # skip empty string
            if string:
                itr = itertools.chain((string,), itr)
        except StopIteration:
            pass
    return itr


def _iglob(pathname, root_dir, recursive, dironly, include_hidden=False):
    # pylint: disable=too-many-branches

    dirname, basename = os.path.split(pathname)
    if not has_magic(pathname):
        assert not dironly
        if basename:
            if _lexists(_join(root_dir, pathname)):
                yield pathname
        else:
            # Patterns ending with a slash should match only directories
            if _isdir(_join(root_dir, dirname)):
                yield pathname
        return
    if not dirname:
        if recursive and _isrecursive(basename):
            yield from _glob2(root_dir, basename, dironly, include_hidden=include_hidden)
        else:
            yield from _glob1(root_dir, basename, dironly, include_hidden=include_hidden)
        return
    # `os.path.split()` returns the argument itself as a dirname if it is a
    # drive or UNC path.  Prevent an infinite recursion if a drive or UNC path
    # contains magic characters (i.e. r'\\?\C:').
    if dirname != pathname and has_magic(dirname):
        dirs = _iglob(dirname, root_dir, recursive, True, include_hidden=include_hidden)
    else:
        dirs = [dirname]
    if has_magic(basename):
        if recursive and _isrecursive(basename):
            glob_in_dir = _glob2
        else:
            glob_in_dir = _glob1
    else:
        glob_in_dir = _glob0
    for dirname in dirs:
        for name in glob_in_dir(_join(root_dir, dirname),
                                basename,
                                dironly,
                                include_hidden=include_hidden):
            yield os.path.join(dirname, name)


# These 2 helper functions non-recursively glob inside a literal directory.
# They return a list of basenames.  _glob1 accepts a pattern while _glob0
# takes a literal basename (so it only has to check for its existence).


def _glob1(dirname, pattern, dironly, include_hidden=False):
    names = _listdir(dirname, dironly)
    if include_hidden or not _ishidden(pattern):
        names = (x for x in names if include_hidden or not _ishidden(x))
    return fnmatch.filter(names, pattern)


def _glob0(dirname, basename, dironly, include_hidden=False):  # pylint: disable=unused-argument
    if basename:
        if _lexists(_join(dirname, basename)):
            return [basename]
    else:
        # `os.path.split()` returns an empty basename for paths ending with a
        # directory separator.  'q*x/' should match only directories.
        if _isdir(dirname):
            return [basename]
    return []


# Following functions are not public but can be used by third-party code.


def glob0(dirname, pattern):
    return _glob0(dirname, pattern, None, False)


def glob1(dirname, pattern):
    return _glob1(dirname, pattern, None, False)


# This helper function recursively yields relative pathnames inside a literal
# directory.


def _glob2(dirname, pattern, dironly, include_hidden=False):
    assert _isrecursive(pattern)
    yield pattern[:0]
    yield from _rlistdir(dirname, dironly, include_hidden=include_hidden)


# If dironly is false, yields all file names inside a directory.
# If dironly is true, yields only directory names.
def _iterdir(dirname, dironly: bool):
    try:
        if dirname:
            arg = dirname
        elif isinstance(dirname, bytes):
            arg = bytes(os.curdir, 'ASCII')
        else:
            arg = os.curdir
        with os.scandir(arg) as it:  # pylint: disable=invalid-name
            for entry in it:
                try:
                    if not dironly or entry.is_dir():
                        yield entry.name
                except exceptions.PyOSError:
                    pass
    except exceptions.PyOSError:
        return


def _listdir(dirname, dironly):
    with contextlib.closing(_iterdir(dirname, dironly)) as it:  # pylint: disable=invalid-name
        return list(it)


# Recursively yields relative pathnames inside a literal directory.
def _rlistdir(dirname, dironly, include_hidden=False):
    names = _listdir(dirname, dironly)
    for name in names:
        if include_hidden or not _ishidden(name):
            yield name
            path = _join(dirname, name) if dirname else name
            for pname in _rlistdir(path, dironly, include_hidden=include_hidden):
                yield _join(name, pname)


_lexists = os.path.lexists

_isdir = os.path.isdir


def _join(dirname, basename):
    # It is common if dirname or basename is empty
    if not dirname or not basename:
        return dirname or basename
    return os.path.join(dirname, basename)


magic_check = re.compile('([*?[])')
magic_check_bytes = re.compile(b'([*?[])')


def has_magic(string):
    if isinstance(string, bytes):
        match = magic_check_bytes.search(string)
    else:
        match = magic_check.search(string)
    return match is not None


def _ishidden(path):
    return path[0] in ('.', b'.'[0])


def _isrecursive(pattern):
    if isinstance(pattern, bytes):
        return pattern == b'**'

    return pattern == '**'


def escape(pathname):
    """Escape all special characters.
    """
    # Escaping is done by wrapping any of "*?[" between square brackets.
    # Metacharacters do not work in the drive part and shouldn't be escaped.
    drive, pathname = os.path.splitdrive(pathname)
    if isinstance(pathname, bytes):
        pathname = magic_check_bytes.sub(br'[\1]', pathname)
    else:
        pathname = magic_check.sub(r'[\1]', pathname)
    return drive + pathname
