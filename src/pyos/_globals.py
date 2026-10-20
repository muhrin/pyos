"""The global pyOS session.

Everything in pyOS works on a :class:`pyos.Session` (see :mod:`pyos._sessions`), which pairs a
mincePy historian with a current working directory.  There are two ways of choosing a session:

* **Explicitly**: the library layers (:mod:`pyos.db` and :mod:`pyos.fs`) take an optional
  ``session`` argument.  Pass one to work with a particular database, e.g. to use several at once
  (this is what ``rsync`` does to copy between a source and a destination).
* **Implicitly**: when no session is passed, and always in the user facing layers
  (:mod:`pyos.os`, :mod:`pyos.pathlib` and the ``psh`` commands, which, like Python's own ``os``
  module, act on the "current" state), the global session from this module is used.

The global session is set by :func:`connect` or :func:`init` (with ``use_globally=True``, the
default).  If pyOS is used before either has been called, :func:`get_global_session` connects
to the default archive (that of mincePy, e.g. given by ``MINCEPY_ARCHIVE``) so that interactive
use just works.  Code that only wants to know whether there is a session (e.g. the shell prompt)
should pass ``create=False``.
"""

from typing import TYPE_CHECKING, Final, Literal, Optional, overload
from urllib import parse

import mincepy

from . import _sessions, db

if TYPE_CHECKING:
    import pyos

__all__ = "connect", "init", "get_global_session", "reset_global_session"


DEFAULT_DB: Final[str] = "pyos"
_GLOBAL_SESSION: Optional["pyos.Session"] = None


def connect(uri: str = "", use_globally=True) -> "pyos.Session":
    """Connect to an archive and start a session with it

    :param uri: the archive URI (by default that of mincePy, e.g. given by ``MINCEPY_ARCHIVE``)
    :param use_globally: if True, this becomes the global session
    """
    parsed = parse.urlparse(uri)
    historian = mincepy.connect(parsed, use_globally=use_globally)

    return init(historian, use_globally)


def init(historian: mincepy.Historian = None, use_globally=True) -> "pyos.Session":
    """Start a session with the given historian, making sure its database is ready for pyOS

    :param historian: the historian to use (by default the global mincePy historian, which is
        connected to the default archive if there isn't one)
    :param use_globally: if True, this becomes the global session
    """
    global _GLOBAL_SESSION  # noqa: PLW0603
    historian = historian or mincepy.get_historian()

    db.schema.ensure_up_to_date(historian)

    # Create the global session
    session = _sessions.Session(historian)

    if use_globally:
        _GLOBAL_SESSION = session

    return session


def get_historian() -> mincepy.Historian:
    """Get the historian of the global session"""
    return get_global_session().historian


@overload
def get_global_session(create: Literal[True] = True) -> "pyos.Session": ...


@overload
def get_global_session(create: bool) -> Optional["pyos.Session"]: ...


def get_global_session(create: bool = True) -> Optional["pyos.Session"]:
    """Get the global session

    :param create: if True and there is no global session, start one (see :func:`init`).  Pass
        False to just check whether there is one.
    """
    if _GLOBAL_SESSION is None and create:
        init()

    return _GLOBAL_SESSION


def reset_global_session():
    """Close the global session (if there is one).  The next use of pyOS will start a new one"""
    global _GLOBAL_SESSION  # noqa: PLW0603
    if _GLOBAL_SESSION is not None:
        _GLOBAL_SESSION.close()
        _GLOBAL_SESSION = None
