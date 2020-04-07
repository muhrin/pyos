__all__ = ('IsADirectory',)


class PyOSError(Exception):
    """Raised when there is a PyOS exception"""


class IsADirectory(PyOSError):
    """Raise when a file is expected but a directory was passed"""
