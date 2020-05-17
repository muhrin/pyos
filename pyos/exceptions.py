__all__ = 'PyOSError', 'IsADirectoryError', 'NotADirectoryError', 'FileNotFoundError'

# pylint: disable=redefined-builtin


class PyOSError(Exception):
    """Raised when there is a PyOS exception"""


class IsADirectoryError(PyOSError):
    """Raise when a file is expected but a directory was passed"""


class NotADirectoryError(PyOSError):
    """Raise when a directory is expected but a file was passed"""


class FileNotFoundError(PyOSError):  # pylint: disable=redefined-builtin
    """A file was not found"""
