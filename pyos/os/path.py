# -*- coding: utf-8 -*-
"""Pyos versions os python's os.path methods"""
# from . pathlib import *
from .nodb import sep, curdir, pardir, isabs, join, normpath, basename, dirname, split, commonprefix, splitdrive
from .withdb import exists, expanduser, isdir, abspath, relpath, lexists, isfile

__all__ = ('sep', 'curdir', 'pardir', 'isabs', 'abspath', 'join', 'normpath', 'basename', 'dirname',
           'exists', 'lexists', 'expanduser', 'split', 'relpath', 'commonprefix', 'isdir', 'isfile',
           'splitdrive')
