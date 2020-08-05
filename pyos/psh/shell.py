import sys

from . import base

try:
    from . import minki
except ImportError:
    minki = None

__all__ = ('PyosShell',)


class PyosShell(base.BaseShell):
    # pylint: disable=too-few-public-methods

    if minki is not None:
        do_workon = minki.do_workon


if __name__ == '__main__':
    app = PyosShell()
    sys.exit(app.cmdloop())
