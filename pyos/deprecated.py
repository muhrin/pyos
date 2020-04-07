import deprecation

from . import pathlib

from .version import __version__

__all__ = ('working_path',)


@deprecation.deprecated(deprecated_in="0.5.0",
                        removed_in="0.6.0",
                        current_version=__version__,
                        details="Use pyos.pathlib.working_path")
def working_path(path: pathlib.Path):
    return pathlib.working_path(path)
