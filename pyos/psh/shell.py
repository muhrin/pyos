import logging
import sys

from . import base

__all__ = ('PyosShell',)

PyosShell = base.BaseShell

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    app = PyosShell()
    sys.exit(app.cmdloop())
