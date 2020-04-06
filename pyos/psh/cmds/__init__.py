"""Module for built-in commands"""

# Commands:
from .cat import cat
from .cd import cd
from .find import find
from .history import history
from .load import load
from .locate import locate
from .ls import ls
from .meta import meta
from .mv import mv
from .oid import oid
from .pwd import pwd
from .rm import rm
from .save import save
from .tree import tree

__all__ = ('cat', 'cd', 'find', 'history', 'load', 'ls', 'locate', 'meta', 'mv', 'oid', 'pwd', 'rm',
           'save', 'tree')
