import sys

from . import base
from . import cmds

try:
    from . import minki
except ImportError:
    minki = None

__all__ = ('PyosShell',)


class PyosShell(base.BaseShell):
    # pylint: disable=too-few-public-methods
    do_cd = cmds.do_cd
    do_cat = cmds.do_cat
    do_ls = cmds.do_ls
    do_mv = cmds.do_mv
    do_pwd = cmds.do_pwd
    do_rm = cmds.do_rm
    do_tree = cmds.do_tree

    if minki is not None:
        do_workon = minki.do_workon


if __name__ == '__main__':
    app = PyosShell()  # pylint: disable=invalid-name
    sys.exit(app.cmdloop())
