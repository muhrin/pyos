from . import psh, version
from .pathlib import Path, PurePath  # pylint: disable=unused-import
from .psh import *  # pylint: disable=unused-wildcard-import, wildcard-import

__all__ = psh.__all__ + ("PurePath", "Path")


def _mod() -> str:
    """Get the message of the day string"""
    return f"Welcome to\n{version.BANNER}"


print(_mod())
