import abc
from typing import Union

__all__ = 'PathLike', 'PathSpec'


class PathLike(metaclass=abc.ABCMeta):
    """An abstract base class for objects representing a pyos path, e.g. pyos.pathlib.PurePath."""

    @abc.abstractmethod
    def __fspath__(self) -> str:
        """Return the pyos path representation of the object."""


PathSpec = Union[str, PathLike]
