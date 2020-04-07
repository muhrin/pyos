"""Module that deals with directories and paths"""
import contextlib
import typing
from typing import Sequence
import uuid

import mincepy

import pyos

__all__ = ('Path', 'PurePath')


class PurePath(pyos.os.PathLike):
    """A path in PyOS.  Where possible the convention follows that of a PurePosixPath in pathlib.
    The one major exception is that folders are represented with an explicit trailing '/' and
    anything else is a file.

    This is a 'pure' path in a similar sense to pathlib.PurePath in that it does not interact with
    the database at all.
    """

    def __init__(self, path='./'):
        super().__init__()
        self._path = pyos.os.path.normpath(path)

    @property
    def parts(self) -> typing.Tuple[str]:
        parts = list(self._path.split('/'))
        for idx in range(len(parts) - 1):
            parts[idx] += '/'
        if PurePath.is_dir(self):
            parts.pop()

        return tuple(parts)

    @property
    def parent(self):
        parts = self.parts

        if self.is_absolute():
            if len(parts) == 1:
                return self.__class__(self.root)

            return self.__class__(''.join(parts[:-1]))

        # Relative path
        if len(parts) == 1:
            return self.__class__()

        return self.__class__(''.join(parts[:-1]))

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
        return self.parts[-1]

    @property
    def root(self) -> str:
        return "/"

    def __fspath__(self):
        return self._path

    def __hash__(self):
        return self._path.__hash__()

    def __eq__(self, other):
        if not isinstance(other, PurePath):
            return False

        return self._path == other._path

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self._path)

    def __str__(self):
        return self._path

    def __truediv__(self, other):
        if not isinstance(other, Path):
            if isinstance(other, str):
                other = self.__class__(other)
            else:
                raise TypeError("Cannot join a path with a '{}'".format(type(other)))

        if self.is_file():
            raise ValueError("Can't join a file with another path")

        if other.is_absolute():
            return other

        return self.__class__(str(self) + str(other))

    def is_file(self) -> bool:
        return not self.is_dir()

    def is_dir(self) -> bool:
        return self._path.endswith(pyos.os.sep)

    def is_absolute(self) -> bool:
        return pyos.os.path.isabs(self._path)

    def to_dir(self):
        """If this path is a file then a directory with the same name (and path) will be returned.
        Otherwise this path will be returned"""
        if PurePath.is_dir(self):
            return self

        return self.__class__(str(self) + '/')

    def to_file(self):
        """If this path is a directory then a file with the same name (and path) will be returned.
        Otherwise this path will be returned"""
        if self.is_file():
            return self

        return self.__class__(str(self)[:-1])

    def resolve(self):
        """Make the path absolute eliminating any . and .. that occur in the path"""
        path = pyos.os.path.abspath(self)
        return self.__class__(path)

    def joinpath(self, *other):
        return self.__class__(pyos.os.path.join(self, *other))


class Path(PurePath, mincepy.BaseSavableObject):
    """A path in Pyos.  Where possible the convention follows that of a PurePosixPath in pathlib.
    The one major exception is that folders are represented with an explicit trailing '/' and
    anything else is a file."""
    ATTRS = ('_path',)
    TYPE_ID = uuid.UUID('5eac541e-848c-43aa-818d-50cf8a2b8507')

    def is_file(self) -> bool:
        """Returns True if this path points to a file that exists"""
        return super(Path, self).is_file() and self.exists()

    def is_dir(self) -> bool:
        """Returns True if this path points to a directory that exists"""
        return super(Path, self).is_dir() and self.exists()

    def exists(self) -> bool:
        """Test whether a path point exists"""
        return pyos.os.path.exists(self)


@contextlib.contextmanager
def working_path(path: pyos.os.PathSpec):
    orig = pyos.os.getcwd()
    pyos.os.chdir(path)
    try:
        yield path
    finally:
        pyos.os.chdir(orig)
