"""Datastructures and functions to deal with results"""
from pathlib import PurePosixPath
from typing import MutableSequence

import tabulate

import mincepy

from . import fmt

__all__ = 'ObjIdList'


class ObjIdList(MutableSequence):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._hist = mincepy.get_historian()
        self._ids = []
        self._table = None
        self._show_loaded = False
        self._show_types = False
        self._show_mtime = False
        self._show_user = False
        self._show_version = False

        self.extend(list(*args, **kwargs))

    def refresh(self):
        self._table = None

    @property
    def table(self):
        return self._table

    @property
    def show_loaded(self) -> bool:
        return self._show_loaded

    @show_loaded.setter
    def show_loaded(self, value: bool):
        self._show_loaded = value
        self._table = None

    @property
    def show_types(self):
        return self._show_types

    @show_types.setter
    def show_types(self, value):
        self._show_types = value
        self._table = None

    @property
    def show_mtime(self):
        return self._show_mtime

    @show_mtime.setter
    def show_mtime(self, value):
        self._show_mtime = value
        self._table = None

    @property
    def show_user(self):
        return self._show_user

    @show_user.setter
    def show_user(self, value):
        self._show_user = value
        self._table = None

    @property
    def show_version(self):
        return self._show_version

    @show_version.setter
    def show_version(self, value):
        self._show_version = value
        self._table = None

    def _generate_repr(self):
        table = []
        records = {
            record.obj_id: record for record in self._hist.archive.find(obj_id={'$in': self._ids})
        }

        for obj_id in self._ids:
            row = []
            record = records.get(obj_id, None)  # type: mincepy.DataRecord

            if self.show_loaded:
                try:
                    self._hist.get_obj(obj_id)
                    is_loaded = '*'
                except mincepy.NotFound:
                    is_loaded = '-'
                row.append(is_loaded)

            if self.show_types:
                type_str = ''
                if record is not None:
                    try:
                        type_str = fmt.pretty_type_string(
                            self._hist.get_helper(record.type_id).TYPE)
                    except TypeError:
                        type_str = str(record.type_id)
                row.append(type_str)

            if self.show_mtime:
                mtime_str = ''
                if record is not None:
                    mtime_str = fmt.pretty_datetime(record.snapshot_time)
                row.append(mtime_str)

            if self.show_user:
                user_str = ''
                if record is not None:
                    user_str = fmt.pretty_datetime(record.get_extra(mincepy.ExtraKeys.USER))
                row.append(user_str)

            if self.show_version:
                version = ''
                if record is not None:
                    version = record.version
                row.append(version)

            row.append(str(obj_id))
            table.append(row)

        self._table = table

    def __add__(self, other):
        if isinstance(other, ObjIdList):
            return ObjIdList(self._ids + other._ids)

        raise TypeError("Cannot add to type '{}'".format(type(other)))

    def __repr__(self) -> str:
        if self._table is None:
            self._generate_repr()

        return tabulate.tabulate(self.table, tablefmt="plain")

    def __getitem__(self, item):
        return self._ids.__getitem__(item)

    def __setitem__(self, key, value):
        value = self._hist._ensure_obj_id(value)
        self._ids.__setitem__(key, value)

    def __delitem__(self, key):
        return self._ids.__delitem__(key)

    def __len__(self):
        return self._ids.__len__()

    def insert(self, i: int, item):
        item = self._hist._ensure_obj_id(item)
        self._ids.insert(i, item)


class PathList(MutableSequence):

    def __init__(self, *args, **kwargs):
        super().__init__()

        self._hist = mincepy.get_historian()
        self._paths = []

        self.extend(list(*args, **kwargs))

    def table(self):
        return [str(path) for path in self._path]

    def __repr__(self) -> str:
        return tabulate.tabulate(self.table, tablefmt="plain")

    def __getitem__(self, item):
        return self._paths.__getitem__(item)

    def __setitem__(self, key, value):
        self._paths.__setitem__(key, PurePosixPath(value))

    def __delitem__(self, key):
        return self._paths.__delitem__(key)

    def __len__(self):
        return self._paths.__len__()

    def insert(self, i: int, item):
        self._paths.insert(i, PurePosixPath(item))


class ObjIdPathList(MutableSequence):

    def __init__(self, *args, **kwargs):
        super().__init__()

        self._obj_ids = ObjIdList()
        self._paths = PathList()

        self.extend(list(*args, **kwargs))

    def __repr__(self) -> str:
        table = self._obj_ids.table
        cols = 2
        if table:
            cols = len(table[0])

        return tabulate.tabulate(table, tablefmt="plain")

    def __getitem__(self, item):
        return self._paths.__getitem__(item)

    def __setitem__(self, key, value):
        self._paths.__setitem__(key, PurePosixPath(value))

    def __delitem__(self, key):
        return self._paths.__delitem__(key)

    def __len__(self):
        return self._paths.__len__()

    def insert(self, i: int, item):
        self._paths.insert(i, PurePosixPath(item))
