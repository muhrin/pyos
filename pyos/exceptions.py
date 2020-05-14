__all__ = ('PyOSError', 'IsADirectory', 'FileNotFoundError')


class PyOSError(Exception):
    """Raised when there is a PyOS exception"""


class IsADirectory(PyOSError):
    """Raise when a file is expected but a directory was passed"""


class FileNotFoundError(PyOSError):  # pylint: disable=redefined-builtin
    """A file was not found"""
