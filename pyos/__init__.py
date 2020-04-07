from . import version
"""

                  ____  ____
                 / __ \/ __ /
    ____  __  __/ / / / /_
   / __ \/ / / / / / /\__ \
  / /_/ / /_/ / /_/ /___/ /
 / .___/\__, /\____//____/
/_/    /____/                 v{}


A new way to interact with your python objects.  PyOS allows you to treat python objects in a 
similar way to the way you interact with files on your filesystem at the moment except in an ipython
console or script.  Objects are stored in a database and presented to the user as existing in a
virtual file system.  Many of the familiar *nix commands are available (ls, mv, rm, tree, cat, find)
except they take on a new, more powerful form because you're in a fully fledged python environment
and not restricted to just two types (file and directories) like on a traditional filesystem but
indeed any python type that can be stored by PyOS's backend.  
""".format(version.__version__)

# Order is important here, first we list all the 'base' modules, then the rest
from . import exceptions
from . import os
from . import db
from . import pathlib
from . import fs

from . import config
from . import fmt
from . import lib
from . import psh
from . import psh_lib

from .version import *
from .lib import *
from .exceptions import *
from .deprecated import working_path
from .pathlib import PurePath, Path

_MODULES = 'os', 'config', 'db', 'fmt', 'fs', 'pathlib', 'psh_lib', 'psh'
_DEPRECATED = ('working_path',)
_ADDITIONAL = ('PurePath', 'Path')

__all__ = version.__all__ + lib.__all__ + exceptions.__all__ + _MODULES + _DEPRECATED + _ADDITIONAL
