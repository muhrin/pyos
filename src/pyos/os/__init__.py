"""Classes and functions related to pyos' virtual filesystem.  This module is modelled on python's
os module and users familiar that will find many of the methods familiar."""

# pylint: disable=cyclic-import

from . import path, types
from .nodb import DirEntry, curdir, fsdecode, fsencode, fspath, pardir, sep
from .types import *
from .withdb import chdir, getcwd, isdir, listdir, makedirs, remove, rename, scandir, unlink

_ADDITIONAL = (
    "path",
    "getcwd",
    "chdir",
    "fspath",
    "listdir",
    "remove",
    "sep",
    "unlink",
    "curdir",
    "pardir",
    "rename",
    "scandir",
    "DirEntry",
    "isdir",
    "makedirs",
    "fsencode",
    "fsdecode",
)

__all__ = types.__all__ + _ADDITIONAL  # pylint: disable=undefined-variable
