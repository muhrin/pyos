import sys

from . import base
from . import cmds


class PyosShell(base.BaseShell):
    do_cd = cmds.do_cd
    do_cat = cmds.do_cat
    do_ls = cmds.do_ls
    do_mv = cmds.do_mv
    do_pwd = cmds.do_pwd
    do_rm = cmds.do_rm
    do_tree = cmds.do_tree


if __name__ == '__main__':
    app = PyosShell()  # pylint: disable=invalid-name
    sys.exit(app.cmdloop())
