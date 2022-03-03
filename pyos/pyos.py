# -*- coding: utf-8 -*-
from . import db
from . import psh
from . import version
from .psh import *  # pylint: disable=unused-wildcard-import, wildcard-import
from .pathlib import PurePath, Path  # pylint: disable=unused-import

__all__ = psh.__all__ + ('PurePath', 'Path')


def _mod() -> str:
    """Get the message of the day string"""
    return f'Welcome to\n{version.BANNER}'


print(_mod())
db.init()
