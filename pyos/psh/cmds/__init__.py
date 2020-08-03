"""Module for built-in commands"""

# Commands:
from .cat import cat, do_cat
from .cd import cd, do_cd
from .find import find, do_find
from .history import history
from .load import load
from .locate import locate
from .ls import ls, do_ls
from .meta import meta
from .mv import mv, do_mv
from .oid import oid
from .pwd import pwd, do_pwd
from .rm import rm, do_rm
from .save import save
from .tree import tree, do_tree

__all__ = ('cat', 'cd', 'find', 'history', 'load', 'ls', 'locate', 'meta', 'mv', 'oid', 'pwd', 'rm',
           'save', 'tree')
