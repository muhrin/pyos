import datetime
import inspect
import typing

import mincepy


def pretty_type_string(obj_type: typing.Type) -> str:
    """Given an type will return a simple type string"""
    type_str = str(obj_type)
    if type_str.startswith('<class '):
        return type_str[8:-2]
    return type_str


def format_record(record: mincepy.DataRecord, user=False, ctime=False, version=False) -> list:
    hist = mincepy.get_historian()
    try:
        type_str = pretty_type_string(hist.get_helper(record.type_id).TYPE)
    except TypeError:
        type_str = str(record.type_id)

    data = []
    data.append(type_str)

    if user:
        data.append(record.get_extra(mincepy.ExtraKeys.USER))

    if version:
        data.append(record.version)

    if ctime:
        data.append(pretty_datetime(record.creation_time))

    try:
        hist.get_obj(record.obj_id)
        is_loaded = True
    except mincepy.NotFound:
        is_loaded = False

    data.append(record.obj_id)
    data.append('*' if is_loaded else '')

    return data


def obj_dict(obj):
    """Given an object return a dictionary that represents it"""
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
