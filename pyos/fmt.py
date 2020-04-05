import datetime
import inspect
import typing
from typing import Mapping


def pretty_type_string(obj_type: typing.Type) -> str:
    """Given an type will return a simple type string"""
    type_str = str(obj_type)
    if type_str.startswith('<class '):
        type_str = type_str[8:-2]

    parts = type_str.split('.')
    if len(parts) > 2:
        return "|".join([parts[0], parts[-1]])

    return type_str


def obj_dict(obj):
    """Given an object return a dictionary that represents it"""
    if isinstance(obj, Mapping):
        return dict(obj)

    repr_dict = {}
    for name in dir(obj):
        if not name.startswith('_'):
            try:
                value = getattr(obj, name)
                if not inspect.isroutine(value):
                    repr_dict[name] = value
            except Exception as exc:  # pylint: disable=broad-except
                repr_dict[name] = '{}: {}'.format(type(exc).__name__, exc)

    return repr_dict


def pretty_datetime(value) -> str:
    if isinstance(value, type):
        return pretty_type_string(value)
    if isinstance(value, datetime.datetime):
        if value.year == datetime.datetime.now().year:
            fmt = "%b %d %H:%M"
        else:
            fmt = "%b %d %Y"

        return value.strftime(fmt)

    return str(value)
