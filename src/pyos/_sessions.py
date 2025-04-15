import getpass
from typing import TYPE_CHECKING, Sequence

import mincepy
import mincepy.archives

from . import db

if TYPE_CHECKING:
    import pyos

__all__ = ("Session",)


class Session(mincepy.archives.ArchiveListener):

    def __init__(self, historian: mincepy.Historian, cwd: "pyos.os.PathSpec" = None):
        """Start a new session"""
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
        return db.save_one(obj, path, overwrite=overwrite, meta=meta)

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
                ]
            )

        if deleted_objects:
            db.fs.remove_objs(tuple(deleted_objects))


def _get_homedir() -> "pyos.db.fs.Path":
    """Get the home directory for the current user"""
    return "/", getpass.getuser()
