"""Module with convenience functions for building queries"""

from .constants import DIR_KEY


def subdirs(root: str, start_depth=1, end_depth=1) -> dict:
    """Get a query string that will look for subdirectories of root optionally specifying the
    start and end depths
    """
    regex = ('^{}([^/]+/){{{},{}}}$'.format(root, start_depth, end_depth))
    return {DIR_KEY: {'$regex': regex}}
