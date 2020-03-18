"""Module with convenience functions for building queries"""
from typing import Iterable

from .constants import DIR_KEY


def or_(*conditions):
    if len(conditions) == 1:
        return conditions[0]

    return {'$or': list(conditions)}


def and_(*conditions):
    return {'$and': list(conditions)}


def unset_(*keys: Iterable[str]):
    return {'$unset': {key: '' for key in keys}}


def subdirs(root: str, start_depth=1, end_depth=1) -> dict:
    """Get a query string that will look for subdirectories of root optionally specifying the
    start and end depths
    """
    if end_depth == -1:
        end_depth = ''  # This will cause the regex to allow any number of repetitions
    regex = ('^{}([^/]+/){{{},{}}}$'.format(root, start_depth, end_depth))
    return {DIR_KEY: {'$regex': regex}}


def dirmatch(directory: str) -> dict:
    """Get the query dictionary to search in a particular directory"""
    query = {DIR_KEY: str(directory)}
    if directory == "/":
        # Special case for root: all objects that have no DIR_KEY are by default
        # considered to be in the root
        query = or_(query, {DIR_KEY: {'$exists': False}})
    return query
