import deprecation

from . import fs

from .version import __version__

__all__ = ('working_path',)


@deprecation.deprecated(deprecated_in="0.5.0",
                        removed_in="0.6.0",
                        current_version=__version__,
                        details="Use pyos.fs.working_path")
def working_path(path: fs.PyosPath):
    return fs.working_path(path)
