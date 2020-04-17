"""Module with convenience functions for building queries"""
from typing import Iterable

import pyos


def or_(*conditions):
    if len(conditions) == 1:
        return conditions[0]

    return {'$or': list(conditions)}


def and_(*conditions):
    if len(conditions) == 1:
        return conditions

    return {'$and': list(conditions)}


def unset_(*keys: Iterable[str]):
    return {'$unset': {key: '' for key in keys}}


def in_(*args):
    if len(args) == 1:
        return args[0]

    return {'$in': list(args)}


def gt(val):  # pylint: disable=invalid-name
    return {'$gt': val}


gt_ = gt  # pylint: disable=invalid-name


def subdirs(root: str, start_depth=1, end_depth=1) -> dict:
    """Get a query string that will look for subdirectories of root optionally specifying the
    start and end depths
    """
    if end_depth == -1:
        end_depth = ''  # This will cause the regex to allow any number of repetitions
    regex = ('^{}([^/]+/){{{},{}}}$'.format(root, start_depth, end_depth))
    return {pyos.config.DIR_KEY: {'$regex': regex}}


def dirmatch(directory: str) -> dict:
    """Get the query dictionary to search in a particular directory"""
    query = {pyos.config.DIR_KEY: str(directory)}
    if directory == "/":
        # Special case for root: all objects that have no DIR_KEY are by default
        # considered to be in the root
        query = or_(query, {pyos.config.DIR_KEY: {'$exists': False}})
    return query
