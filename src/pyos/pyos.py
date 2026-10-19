from . import psh, version
from .pathlib import Path, PurePath
from .psh import *

__all__ = psh.__all__ + ("PurePath", "Path")


def _mod() -> str:
    """Get the message of the day string"""
    return f"Welcome to\n{version.BANNER}"


print(_mod())
