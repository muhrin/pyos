r"""A new way to interact with your python objects.

PyOS allows you to treat python objects in a similar way to the way you interact with files on your
filesystem at the moment except in an ipython console or script.  Objects are stored in a database
and presented to the user as existing in a virtual file system.  Many of the familiar ``*nix``
commands are available (``ls``, ``mv``, ``rm``, ``tree``, ``cat``, ``find``) except they take on a
new, more powerful form because you're in a fully fledged python environment and not restricted to
just two types (file and directories) like on a traditional filesystem but indeed any python type
that can be stored by PyOS's backend.

::

                      ____  ____
                     / __ \/ __ /
        ____  __  __/ / / / /_
       / __ \/ / / / / / /\__ \
      / /_/ / /_/ / /_/ /___/ /
     / .___/\__, /\____//____/
    /_/    /____/
"""

# Order is important here, first we list all the 'base' modules, then the rest
from . import (
    _globals,
    _sessions,
    config,
    db,
    exceptions,
    fmt,
    fs,
    os,
    pathlib,
    psh,
    psh_lib,
    representers,
    results,
    version,
)
from ._globals import *
from ._sessions import *
from .exceptions import *
from .pathlib import Path, PurePath, working_path
from .version import *
from .version import __version__

_MODULES = "os", "config", "db", "fmt", "fs", "pathlib", "psh_lib", "psh"
_DEPRECATED = ("working_path",)
_ADDITIONAL = "PurePath", "Path", "__version__", "connect", "results", "representers"

__all__ = (  # noqa: PLE0605
    _globals.__all__
    + version.__all__
    + exceptions.__all__
    + _sessions.__all__
    + _MODULES
    + _DEPRECATED
    + _ADDITIONAL
)
