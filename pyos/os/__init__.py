# -*- coding: utf-8 -*-
"""Classes and functions related to pyos' virtual filesystem.  This module is modelled on python's
os module and users familiar that will find many of the methods familiar."""
# pylint: disable=cyclic-import

from .types import *
from . import path
from .nodb import fspath, DirEntry, sep, curdir, pardir, fsencode, fsdecode
from .withdb import getcwd, chdir, listdir, remove, unlink, rename, scandir, isdir, makedirs

_ADDITIONAL = ('path', 'getcwd', 'chdir', 'fspath', 'listdir', 'remove', 'sep', 'unlink', 'curdir',
               'pardir', 'rename', 'scandir', 'DirEntry', 'isdir', 'makedirs', 'fsencode',
               'fsdecode')

__all__ = types.__all__ + _ADDITIONAL  # pylint: disable=undefined-variable
