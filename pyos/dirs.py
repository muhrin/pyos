"""Module that deals with directories and paths"""
import getpass
import os
from pathlib import PurePosixPath
import typing

import mincepy

from .constants import DIR_KEY, NAME_KEY
from . import queries

_DIRECTORY = None  # type: typing.Optional[PurePosixPath]


def init():
    cwd()  # Makes sure the directory is set up


def reset():
    global _DIRECTORY
    mincepy.get_historian().meta.sticky.pop(DIR_KEY, None)
    _DIRECTORY = None


def cwd() -> PurePosixPath:
    """Get the current working directory"""
    global _DIRECTORY
    if _DIRECTORY is None:
        cd('/{}'.format(getpass.getuser()))

    return _DIRECTORY


def cd(directory: [str, PurePosixPath]) -> PurePosixPath:
    global _DIRECTORY
    new_dir = abspath(directory)
    mincepy.get_historian().meta.sticky[DIR_KEY] = dirstring(new_dir)
    _DIRECTORY = new_dir
    return _DIRECTORY


def get_contents(path: [str, PurePosixPath] = None) -> [dir, set]:
    """Get the objects and subdirectories given a path"""
    path = path or cwd()
    path = abspath(path)
    hist = mincepy.get_historian()

    metas = hist.meta.find(queries.subdirs(dirstring(path), 0, 1))

    objects = {}
    subdirs = set()

    # Get directories and object ids
    my_dir = dirstring(path)
    for meta in metas:
        directory = meta[DIR_KEY]

        if directory == my_dir:
            obj_id = meta['obj_id']
            obj_name = meta.get(NAME_KEY, None)
            objects[obj_id] = obj_name
        else:
            subdirs.add(directory[len(my_dir):-1])

    return objects, subdirs


def get_obj_id(objname: str, directory: PurePosixPath = None):
    directory = directory or cwd()
    hist = mincepy.get_historian()

    metas = tuple(hist.meta.find({DIR_KEY: dirstring(directory), NAME_KEY: objname}))
    if metas:
        assert len(metas) == 1, "Uniqueness constraint violated"
        return metas[0]['obj_id']

    return None


# region path_utils


def abspath(path: [str, PurePosixPath]) -> PurePosixPath:
    """Given an absolute or relative path returns a normalised absolute path. Any occurences of
    . or .. will be resolved as expected.
    If no directory is supplied the current working directory will be used"""
    if not path:
        return cwd()

    path = PurePosixPath(path)
    if not path.is_absolute():
        path = cwd() / path

    return norm(path)


def norm(path: [str, PurePosixPath]) -> PurePosixPath:
    """Normalise a path, resolving all occurrences of .. and ."""
    return PurePosixPath(os.path.normpath(str(PurePosixPath(path))))


def dirstring(path: PurePosixPath):
    """Get a directory string.  These always end with a trailing '/'"""
    if path == PurePosixPath('/'):
        # Special case for root
        return '/'

    return str(path) + '/'


# endregion


class Directory:

    def __init__(self, name: typing.Union[str, PurePosixPath] = '/'):
        self.__path = abspath(name)

    def __str__(self):
        return str(self.__path)

    def __repr__(self):
        return "Directory('{}')".format(self.__path)

    def __dir__(self) -> typing.Iterable[str]:
        """Get the contents of this directory as attributes.  We make the following mappings which
        also mean that the attributes aren't unambigious but this can be resolved using the dir[]
        notation.

        The attributes are listed in the following priority:
        1. Any objects in the directory are listed as dir._{obj_id}
        2. Any objects with names are listed as dir.{obj_name} _unless_ there is a subdirectory
           with the name {obj_name} in which case it is listed as dir.{obj_name}_{obj_id}
        3. Subdirectories are listed as dir.{dir_name}

        This has the following consequences (amongst others):
        * Directories that have the name {obj_name}_{obj_id} will be hidden by point 2.
        * Directories with the name _{obj_id} will be hidden by point 1.
        """
        objects, subdirs = get_contents(self.__path)

        # Priority 3.
        contents = subdirs

        # Priority 2. Deduplicate names clashing with folders
        for obj_id, name in objects.items():
            if name in contents:
                contents.add("{}_{}".format(name, obj_id))
            elif name:
                contents.add(name)

        # Priority 1. Obj ids
        contents.update("_{}".format(obj_id) for obj_id in objects)

        return contents

    def __getattr__(self, item: str):
        """Uses priorities from __dir__ to get attribute from this directory"""
        hist = mincepy.get_historian()

        if not item:
            raise AttributeError(item)

        # Priority 1. Obj id
        if item[0] == '_':
            try:
                obj_id = hist._ensure_obj_id(item[1:])
            except mincepy.NotFound:
                pass
            else:
                return mincepy.load(obj_id)

        # Priority 2. Objname
        objects, subdirs = get_contents(self.__path)
        # First check for the overwrite case
        parts = item.split("_")
        if len(parts) > 1:
            hist = mincepy.get_historian()
            try:
                obj_id = hist._ensure_obj_id(parts[-1])
            except mincepy.NotFound:
                pass
            else:
                if "_".join(parts[:-1]) in objects.values():
                    return mincepy.load(obj_id)

        # Check the objects for this name
        for obj_id, name in objects.items():
            if item == name:
                return mincepy.load(obj_id)

        # Priority 3. Subdir
        if item in subdirs:
            return Directory(self.__path / item)

        raise AttributeError(item)


class CWD(Directory):

    def __init__(self):
        super(CWD, self).__init__()
        self.__path = property(cwd)
