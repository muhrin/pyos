"""Datastructures and functions to deal with results"""
from collections.abc import MutableSequence
import typing

import mincepy
import tabulate

from . import fmt

__all__ = 'ObjIdList'


class ObjIdList(MutableSequence):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._hist = mincepy.get_historian()
        self._ids = []
        self._repr = None
        self._show_loaded = False
        self._show_types = False
        self._show_mtime = False
        self._show_user = False
        self._show_version = False

        self.extend(list(*args, **kwargs))

    def refresh(self):
        self._repr = None

    @property
    def show_loaded(self) -> bool:
        return self._show_loaded

    @show_loaded.setter
    def show_loaded(self, value: bool):
        self._show_loaded = value
        self._repr = None

    @property
    def show_types(self):
        return self._show_types

    @show_types.setter
    def show_types(self, value):
        self._show_types = value
        self._repr = None

    @property
    def show_mtime(self):
        return self._show_mtime

    @show_mtime.setter
    def show_mtime(self, value):
        self._show_mtime = value
        self._repr = None

    @property
    def show_user(self):
        return self._show_user

    @show_user.setter
    def show_user(self, value):
        self._show_user = value
        self._repr = None

    @property
    def show_version(self):
        return self._show_version

    @show_version.setter
    def show_version(self, value):
        self._show_version = value
        self._repr = None

    def _generate_repr(self):
        table = []
        records = {record.obj_id: record
                   for record
                   in self._hist.archive.find(obj_id={'$in': self._ids})}

        for obj_id in self._ids:
            row = []
            record = records.get(obj_id, None)  # type: mincepy.DataRecord

            if self.show_loaded:
                try:
                    self._hist.get_obj(obj_id)
                    is_loaded = '*'
                except mincepy.NotFound:
                    is_loaded = ''
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

        self._repr = tabulate.tabulate(table, tablefmt="plain")

    def __repr__(self) -> str:
        if self._repr is None:
            self._generate_repr()
        return self._repr

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
