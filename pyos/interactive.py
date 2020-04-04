from . import cmd
from .cmd import *  # pylint: disable=unused-wildcard-import, wildcard-import
from . import version

__all__ = cmd.__all__


def _mod() -> str:
    """Get the message of the day string"""
    return "Welcome to\n{}".format(version.BANNER)


print(_mod())
