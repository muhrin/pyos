"""Sessions: the state that pyOS works with.

A :class:`Session` combines a mincePy historian (i.e. a connection to a database) with the pyOS
state that goes with it, currently the working directory.  Any number of sessions can exist at
the same time, each with their own database and working directory, and the functions in
:mod:`pyos.db` and :mod:`pyos.fs` accept the session to use.  See :mod:`pyos._globals` for how the
global (default) session is chosen.

A session also keeps the pyOS filesystem in step with its database: it listens to the archive so
that objects saved through its historian by any means (e.g. directly with mincePy, or as
references of other objects) are given a path in the session's working directory, and objects
that are deleted are removed from the filesystem.
"""

import getpass
from typing import TYPE_CHECKING, Sequence

import mincepy
import mincepy.archives

from . import db

if TYPE_CHECKING:
    import pyos

__all__ = ("Session",)


class Session(mincepy.archives.ArchiveListener):
    """A pyOS session: a historian together with a current working directory.

    Sessions are normally created with :func:`pyos.connect` or :func:`pyos.init`.  They can be used
    as context managers, in which case they are closed on exit::

        with pyos.connect("litemongo://?engine=memory#scratch", use_globally=False) as session:
            pyos.db.save_one(car, "my_car", session=session)
    """

    def __init__(self, historian: mincepy.Historian, cwd: "pyos.os.PathSpec" = None):
        """Start a new session

        :param historian: the historian (database connection) to use
        :param cwd: the initial working directory (by default the user's home directory, if it
            exists, otherwise the root)
        """
        self._historian = historian

        self._cwd = None
        if cwd:
            self.set_cwd(cwd)
        else:
            try:
                # Default working directory for a session is simply a folder in root with the
                # user's name
                self.set_cwd(_get_homedir())
            except ValueError:
                self.set_cwd(db.fs.ROOT_PATH)

        historian.archive.add_archive_listener(self)

    def __enter__(self) -> "pyos.Session":
        """Nothing to be done"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def historian(self) -> mincepy.Historian:
        return self._historian

    @property
    def cwd(self) -> "pyos.db.fs.Path":
        return self._cwd

    def set_cwd(self, path: "pyos.os.PathSpec"):
        """Set the current working directory"""
        if db.fs.find_entry(path, session=self) is None:
            raise ValueError(f"Path does not exist: {path}")

        self._cwd = path

    def save(
        self,
        obj: object,
        path: "pyos.os.PathSpec" = None,
        overwrite=False,
        meta: dict = None,
    ):
        return db.save_one(obj, path, overwrite=overwrite, meta=meta, session=self)

    def close(self):
        """Close this session.  This object cannot be used after this call"""
        self._historian.archive.remove_archive_listener(self)

        del self._cwd
        del self._historian

    def on_bulk_write(self, archive: mincepy.Archive, ops: Sequence[mincepy.operations.Operation]):
        """Called when an archive is about to perform a sequence of write operations but has not
        performed them yet. The listener must not assume that the operations will be completed as
        there are a number of reasons why this process could be interrupted.
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
            db.fs.execute_instructions(
                [
                    db.fs.SetObjPath(obj_id, self._cwd + (str(obj_id),), only_new=True)
                    for obj_id in new_objects
                ],
                session=self,
            )

        if deleted_objects:
            db.fs.remove_objs(tuple(deleted_objects), session=self)


def _get_homedir() -> "pyos.db.fs.Path":
    """Get the home directory for the current user"""
    return "/", getpass.getuser()
