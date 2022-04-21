# -*- coding: utf-8 -*-
import getpass
from typing import Optional, Sequence

import mincepy
import mincepy.archives

from . import schema
from . import fs

__all__ = 'connect', 'init', 'get_historian', 'reset', 'get_session'

_GLOBAL_SESSION: Optional['Session'] = None


class Session(mincepy.archives.ArchiveListener):

    def __init__(self, historian: mincepy.Historian, cwd: fs.Path = None):
        """Start a new session"""
        self._historian = historian

        self._cwd = None
        if cwd:
            self.set_cwd(cwd)
        else:
            try:
                # Default working directory for a session is simply a folder in root with the user's name
                self.set_cwd(_get_homedir())
            except ValueError:
                self.set_cwd(fs.ROOT_PATH)

        historian.archive.add_archive_listener(self)

    @property
    def historian(self) -> mincepy.Historian:
        return self._historian

    @property
    def cwd(self) -> fs.Path:
        return self._cwd

    def set_cwd(self, path: fs.Path):
        """Set the current working directory"""
        if fs.find_entry(path, historian=self._historian) is None:
            raise ValueError(f'Path does not exist: {path}')

        self._cwd = path

    def close(self):
        """Close this session.  This object cannot be used after this call"""
        self._historian.archive.remove_archive_listener(self)

        del self._cwd
        del self._historian

    def on_bulk_write(self, archive: mincepy.Archive, ops: Sequence[mincepy.operations.Operation]):
        """Called when an archive is about to perform a sequence of write operations but has not performed them yet.
        The listener must not assume that the operations will be completed as there are a number of reasons why this
        process could be interrupted.
        """
        assert archive is self._historian.archive
        new_objects = []  # Keep track of the new objects being saved
        deleted_objects = []
        for oper in ops:
            if isinstance(oper, mincepy.operations.Insert):
                if oper.snapshot_id.version == 0:
                    new_objects.append(oper.obj_id)
                elif oper.record.is_deleted_record():
                    deleted_objects.append(oper.obj_id)

        if new_objects:
            fs.execute_instructions([
                fs.SetObjPath(obj_id, self._cwd + (str(obj_id),), only_new=True)
                for obj_id in new_objects
            ])

        if deleted_objects:
            fs.remove_objs(tuple(deleted_objects))


def connect(uri: str = '', use_globally=True) -> mincepy.Historian:
    historian = mincepy.connect(uri, use_globally=use_globally)
    init(historian, use_globally)

    return historian


def init(historian: mincepy.Historian = None, use_globally=True) -> mincepy.Historian:
    """Initialise a Historian such that it is ready to be used with pyOS"""
    global _GLOBAL_SESSION  # pylint: disable=global-statement
    historian = historian or mincepy.get_historian()

    schema.ensure_up_to_date(historian)

    # Create the global session
    session = Session(historian)

    if use_globally:
        _GLOBAL_SESSION = session

    return historian


def get_historian() -> mincepy.Historian:
    """Get the active historian in pyos"""
    global _GLOBAL_SESSION  # pylint: disable=global-statement, global-variable-not-assigned
    if _GLOBAL_SESSION is None:
        raise RuntimeError(
            'A global pyOS session has not been initialised.  Call connect() or init() first.')

    return _GLOBAL_SESSION.historian


def get_session() -> Session:
    global _GLOBAL_SESSION  # pylint: disable=global-variable-not-assigned
    return _GLOBAL_SESSION


def reset():
    global _GLOBAL_SESSION  # pylint: disable=global-statement, global-variable-not-assigned
    if _GLOBAL_SESSION is not None:
        _GLOBAL_SESSION.close()


def _get_homedir() -> fs.Path:
    """Get the home directory for the current user"""
    return (
        '/',
        getpass.getuser(),
    )
