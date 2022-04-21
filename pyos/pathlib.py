# -*- coding: utf-8 -*-
"""Module that deals with directories and paths"""
import contextlib
import pathlib
from typing import Sequence, Iterable, Tuple, Union
import uuid

import deprecation
import mincepy

from pyos import exceptions
from pyos import fs
from pyos import os
from pyos import version

__all__ = ('Path', 'PurePath')


class PurePath(os.PathLike):
    """A path in PyOS.  Where possible the convention follows that of a PurePosixPath in pathlib.

    This is a 'pure' path in a similar sense to pathlib.PurePath in that it does not interact with
    the database at all.
    """
    __slots__ = ('_path',)

    def __init__(self, path: os.PathSpec = '.'):
        super().__init__()
        self._path = os.path.normpath(path)

    @property
    def parts(self) -> Tuple[str]:
        return pathlib.PurePosixPath(self._path).parts

    @property
    def parent(self):
        return self.__class__(os.path.dirname(self._path))

    @property
    def parents(self) -> Sequence:
        """Get a sequence of paths that are the parents of this path"""
        current = self.parent
        parents = [current]
        while current.parent != parents[-1]:
            parents.append(current.parent)
            current = parents[-1]
        return parents

    @property
    def name(self):
        return os.nodb.basename(self)

    @property
    def root(self) -> str:
        return '/'

    def __fspath__(self):
        return self._path

    def __hash__(self):
        return self._path.__hash__()

    def __eq__(self, other):
        if not isinstance(other, PurePath):
            return False

        return self._path == other._path

    def __repr__(self):
        return f"{self.__class__.__name__}('{self._path}')"

    def __str__(self):
        return self._path

    def __truediv__(self, other):
        if not isinstance(other, PurePath):
            if not isinstance(other, str):
                raise TypeError(f"Cannot join a path with a '{type(other)}'")

        if os.path.isabs(other):
            return self.__class__(other)

        return self.__class__(os.path.join(str(self), str(other)))

    def is_file_path(self) -> bool:
        """Returns True if this path specifies a file i.e. does not end with a training '/'"""
        return not self.is_dir_path()

    def is_dir_path(self) -> bool:
        """Returns True if this path specified a directory i.e. ends with a trailing '/'"""
        return self._path.endswith(os.sep)

    def is_absolute(self) -> bool:
        return os.path.isabs(self._path)

    @deprecation.deprecated(
        deprecated_in='0.8.0',
        removed_in='0.9.0',
        current_version=version.__version__,
        details='We no longer make a distinction between a file path and dir path')
    def to_dir(self) -> 'PurePath':
        """If this path is a file path then a directory with the same name will be
        returned. Otherwise, this path will be returned"""
        return self

    @deprecation.deprecated(
        deprecated_in='0.8.0',
        removed_in='0.9.0',
        current_version=version.__version__,
        details='We no longer make a distinction between a file path and dir path')
    def to_file(self):
        """If this path is a directory then a file path with the same name will be returned.
        Otherwise, this path will be returned"""
        return self

    def joinpath(self, *other):
        return self.__class__(os.path.join(self, *other))


class Path(PurePath, mincepy.SimpleSavable):
    """A path in Pyos.  Where possible the convention follows that of a PurePosixPath in pathlib.
    The one major exception is that folders are represented with an explicit trailing '/' and
    anything else is a file."""
    ATTRS = ('_path',)
    TYPE_ID = uuid.UUID('5eac541e-848c-43aa-818d-50cf8a2b8507')

    def is_file(self) -> bool:
        """Returns True if this path is a file path and exists"""
        return os.path.isfile(self)

    def is_dir(self) -> bool:
        """Returns True if this path is a directory path and exists"""
        return os.isdir(self)

    def exists(self) -> bool:
        """Test whether a path point exists"""
        return os.path.exists(self)

    def unlink(self, missing_ok=False):
        if not self.exists():
            if missing_ok:
                return
            raise exceptions.FileNotFoundError(f"Can't delete '{self}', it does not exist")

        os.unlink(self)

    def iterdir(self) -> Iterable['Path']:
        """
        When the path points to a directory, yield path objects of the directory contents:

        >>>
        >>> p = Path('docs')
        >>> for child in p.iterdir(): child
        ...
        Path('docs/conf')
        Path('docs/readme')
        Path('docs/index.rst')
        Path('docs/_build')
        Path('docs/_static')
        """
        if not self.is_dir():
            raise exceptions.NotADirectoryError(f'Not a directory: {os.path.relpath(self)}')
        if not self.exists():
            raise exceptions.FileNotFoundError(f"No such directory: '{os.path.relpath(self)}'")

        node = fs.DirectoryNode(self)
        node.expand(1)
        for child in node.children:
            yield child.abspath

    def rename(self, target: os.PathSpec) -> 'Path':
        target = Path(target).resolve()
        os.rename(self._path, target)
        return target

    def resolve(self) -> Union[PurePath, 'Path']:
        """Make the path absolute eliminating any . and .. that occur in the path"""
        path = os.path.abspath(os.path.relpath(self))
        if path == self._path:
            # Avoid constructing a new one as this is currently a little slow
            return self
        return self.__class__(path)


@contextlib.contextmanager
def working_path(path: os.PathSpec):
    """Context manager that changes the current working directory for the duration of the context,
    returning to the previous directory on exiting"""
    orig = os.getcwd()
    os.chdir(path)
    try:
        yield path
    finally:
        os.chdir(orig)
