"""Module that deals with directories and paths"""
import contextlib
import getpass
import os
import typing
import uuid

import mincepy

from .constants import DIR_KEY, NAME_KEY

__all__ = 'PyosPath', 'working_path'

_DIRECTORY = None  # type: typing.Optional[PyosPath]


class PyosPath(mincepy.BaseSavableObject):
    """A path in Pyos.  Where possible the convention follows that of a PurePosixPath in pathlib.
    The one major exception is that folders are represented with an explicit trailing '/' and
    anything else is a file.

    This is a 'pure' path in the pathlib sens in that it does not interact with the database at all
    """
    ATTRS = ('_path',)
    TYPE_ID = uuid.UUID('5eac541e-848c-43aa-818d-50cf8a2b8507')

    def __init__(self, path='./'):
        super().__init__()
        if isinstance(path, PyosPath):
            self._path = path._path
        elif isinstance(path, str):
            if path.endswith('.'):
                path = path + '/'
            self._path = path

    @property
    def parts(self) -> typing.Tuple[str]:
        parts = list(self._path.split('/'))
        if self.is_dir():
            parts.pop()
            parts[-1] = parts[-1] + '/'
            if self.is_absolute():
                parts[0] = '/'

        return tuple(parts)

    @property
    def parent(self):
        return PyosPath("/".join(self.parts[:-1]) + '/')

    @property
    def name(self):
        return self.parts[-1]

    @property
    def root(self) -> str:
        return "/"

    def __hash__(self):
        return self._path.__hash__()

    def __eq__(self, other):
        if not isinstance(other, PyosPath):
            return False

        return self._path == other._path

    def __repr__(self):
        return "PyosPath('{}')".format(self._path)

    def __str__(self):
        return self._path

    def __truediv__(self, other):
        if not isinstance(other, PyosPath):
            if isinstance(other, str):
                other = PyosPath(other)
            else:
                raise TypeError("Cannot join a path with a '{}'".format(type(other)))

        if self.is_file():
            raise ValueError("Can't join a file with another path")

        if other.is_absolute():
            return other

        return PyosPath(str(self) + str(other))

    def is_file(self) -> bool:
        return not self.is_dir()

    def is_dir(self) -> bool:
        return self._path.endswith('/')

    def is_absolute(self) -> bool:
        return self._path.startswith('/')

    def to_dir(self):
        """If this path is a file then a directory with the same name (and path) will be returned.
        Otherwise this path will be returned"""
        if self.is_dir():
            return self

        return PyosPath(str(self) + '/')

    def to_file(self):
        """If this path is a directory then a file with the same name (and path) will be returned.
        Otherwise this path will be returned"""
        if self.is_file():
            return self

        return PyosPath(str(self)[:-1])

    def resolve(self):
        """Make the path absolute eliminating any . and .. that occur in the path"""
        if not self.is_absolute():
            to_norm = cwd() / self
        else:
            to_norm = self

        # Now resolve any . and ..
        normed = os.path.normpath(str(to_norm))
        path = PyosPath(normed)

        if self.is_dir():
            # Re-add back the final slash
            return path.to_dir()

        return path

    def joinpath(self, *other):
        joined = self
        for entry in other:
            joined = joined / entry
        return joined


# The types that can be used to specify a path in PyOs
PathSpec = typing.Union[PyosPath, str]


def init():
    cd('/{}/'.format(getpass.getuser()))


def reset():
    global _DIRECTORY  # pylint: disable=global-statement
    mincepy.get_historian().meta.sticky.pop(DIR_KEY, None)
    _DIRECTORY = None


def cwd() -> PyosPath:
    """Get the current working directory"""
    global _DIRECTORY  # pylint: disable=global-statement
    return _DIRECTORY


def cd(directory: PathSpec) -> PyosPath:  # pylint: disable=invalid-name
    global _DIRECTORY  # pylint: disable=global-statement
    new_dir = PyosPath(directory).resolve()
    assert new_dir.is_dir(), "Cannot change directory to a file path"

    mincepy.get_historian().meta.sticky[DIR_KEY] = str(new_dir)
    _DIRECTORY = new_dir
    return _DIRECTORY


def get_obj_id(objname: str, directory: PathSpec = None):
    directory = (directory or cwd()).resolve()
    hist = mincepy.get_historian()

    metas = tuple(hist.meta.find({DIR_KEY: str(directory), NAME_KEY: objname}))
    if metas:
        assert len(metas) == 1, "Uniqueness constraint violated"
        return metas[0]['obj_id']

    return None


def get_abspath(obj_id, meta: dict):
    assert obj_id, "Must provide a valid obj id"
    meta = meta or {}
    directory = PyosPath(meta.get(DIR_KEY, '/'))
    name = meta.get(NAME_KEY, str(obj_id))
    return directory / name


# class Directory:
#
#     def __init__(self, name: PathSpec = PyosPath('/')):
#         self.__path = name.resolve()
#
#     def __str__(self):
#         return str(self.__path)
#
#     def __repr__(self):
#         return "Directory('{}')".format(self.__path)
#
#     def __dir__(self) -> typing.Iterable[str]:
#         """Get the contents of this directory as attributes.  We make the following mappings which
#         also mean that the attributes aren't unambigious but this can be resolved using the dir[]
#         notation.
#
#         The attributes are listed in the following priority:
#         1. Any objects in the directory are listed as dir._{obj_id}
#         2. Any objects with names are listed as dir.{obj_name} _unless_ there is a subdirectory
#            with the name {obj_name} in which case it is listed as dir.{obj_name}_{obj_id}
#         3. Subdirectories are listed as dir.{dir_name}
#
#         This has the following consequences (amongst others):
#         * Directories that have the name {obj_name}_{obj_id} will be hidden by point 2.
#         * Directories with the name _{obj_id} will be hidden by point 1.
#         """
#         objects, subdirs = get_contents(self.__path)
#
#         # Priority 3.
#         contents = subdirs
#
#         # Priority 2. Deduplicate names clashing with folders
#         for obj_id, name in objects.items():
#             if name in contents:
#                 contents.add("{}_{}".format(name, obj_id))
#             elif name:
#                 contents.add(name)
#
#         # Priority 1. Obj ids
#         contents.update("_{}".format(obj_id) for obj_id in objects)
#
#         return contents
#
#     def __getattr__(self, item: str):
#         """Uses priorities from __dir__ to get attribute from this directory"""
#         hist = mincepy.get_historian()
#
#         if not item:
#             raise AttributeError(item)
#
#         # Priority 1. Obj id
#         if item[0] == '_':
#             try:
#                 obj_id = hist._ensure_obj_id(item[1:])
#             except mincepy.NotFound:
#                 pass
#             else:
#                 return mincepy.load(obj_id)
#
#         # Priority 2. Objname
#         objects, subdirs = get_contents(self.__path)
#         # First check for the overwrite case
#         parts = item.split("_")
#         if len(parts) > 1:
#             hist = mincepy.get_historian()
#             try:
#                 obj_id = hist._ensure_obj_id(parts[-1])
#             except mincepy.NotFound:
#                 pass
#             else:
#                 if "_".join(parts[:-1]) in objects.values():
#                     return mincepy.load(obj_id)
#
#         # Check the objects for this name
#         for obj_id, name in objects.items():
#             if item == name:
#                 return mincepy.load(obj_id)
#
#         # Priority 3. Subdir
#         if item in subdirs:
#             return Directory(self.__path / item)
#
#         raise AttributeError(item)
#
#
# class CWD(Directory):
#
#     def __init__(self):
#         super(CWD, self).__init__()
#         self.__path = property(cwd)


def path_to_meta_dict(path: PathSpec):
    if path is None:
        return {}

    path = path.resolve()
    meta = {}
    if path.is_dir():
        meta[DIR_KEY] = str(path)
    else:
        meta[NAME_KEY] = path.name
        meta[DIR_KEY] = str(path.parent)

    return meta


@contextlib.contextmanager
def working_path(path: PyosPath):
    orig = cwd()
    cd(path)
    try:
        yield path
    finally:
        cd(orig)
