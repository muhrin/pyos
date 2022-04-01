# -*- coding: utf-8 -*-
__all__ = 'PyOSError', 'IsADirectoryError', 'NotADirectoryError', 'FileNotFoundError'

# pylint: disable=redefined-builtin


class PyOSError(Exception):
    """Raised when there is a PyOS exception"""


class IsADirectoryError(PyOSError):  # pylint: disable=redefined-builtin
    """Raise when a file is expected but a directory was passed"""


class NotADirectoryError(PyOSError):  # pylint: disable=redefined-builtin
    """Raise when a directory is expected but a file was passed"""


class FileNotFoundError(PyOSError):  # pylint: disable=redefined-builtin
    """A file was not found"""


class FileExistsError(PyOSError):  # pylint: disable=redefined-builtin
    """Raised when trying to create a file or directory which already exists"""

    def __init__(self, *args, existing_entry_id=None, path=None):
        super().__init__(*args)
        self.entry_id = existing_entry_id
        self.path = path
