"""Module for representers which are used to convert objects into strings"""

import functools
import io
import pprint
from typing import Sequence

import mincepy

try:
    import pyprnt
except ImportError:
    pass

import pyos
from . import utils

__all__ = 'get_default', 'set_default', 'dict_representer', 'make_custom_pyprnt', 'prnt'

_DEFAULT_REPRESENTER = None


def get_default():
    global _DEFAULT_REPRESENTER  # pylint: disable=global-statement
    if _DEFAULT_REPRESENTER is None:
        try:
            # We try importing here just in case the user has since installed pyprnt
            import pyprnt as _  # pylint: disable=import-outside-toplevel
            del _
            return prnt
        except ImportError:
            return dict_representer

    return _DEFAULT_REPRESENTER


def set_default(representer):
    global _DEFAULT_REPRESENTER  # pylint: disable=global-statement
    _DEFAULT_REPRESENTER = representer


def dict_representer(obj):
    try:
        if isinstance(obj, mincepy.File):
            return obj.read_text()

        return pprint.pformat(pyos.fmt.obj_dict(obj))
    except Exception as exc:  # pylint: disable=broad-except
        return str(exc)


def make_custom_pyprnt(**kwargs):
    return functools.partial(pyprnt.prnt, **kwargs)


def _terminal_width_prnt(obj, **kwargs):
    width = utils.get_terminal_width()
    return pyprnt.prnt(obj, end='', width=width, truncate=True, **kwargs)


def prnt(obj, custom_prnt=None):
    """Pyprnt representer.  Use the great pyprnt library to represent the object either as a
    sequence or a dictionary of the public properties.

    See https://github.com/kevink1103/pyprnt for details of pyprnt"""
    to_prnt = to_simple_repr(obj)
    custom_prnt = custom_prnt or _terminal_width_prnt

    buffer = io.StringIO()
    custom_prnt(to_prnt, output=False, file=buffer)
    return buffer.getvalue()


def to_simple_repr(obj):
    """Convert an object into primitive types i.e. str, list, dict, etc"""
    if isinstance(obj, mincepy.File):
        return obj.read_text()

    if isinstance(obj, Sequence):
        return obj

    if isinstance(obj, Exception):
        return "{}: {}".format(obj.__class__.__name__, obj)

    return pyos.fmt.obj_dict(obj)
