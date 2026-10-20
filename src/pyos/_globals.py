from typing import TYPE_CHECKING, Final, Optional
from urllib import parse

import mincepy

from . import _sessions, db

if TYPE_CHECKING:
    import pyos

__all__ = "connect", "init", "get_global_session", "reset_global_session"


DEFAULT_DB: Final[str] = "pyos"
_GLOBAL_SESSION: Optional["pyos.Session"] = None


def connect(uri: str = "", use_globally=True) -> "pyos.Session":
    parsed = parse.urlparse(uri)
    historian = mincepy.connect(parsed, use_globally=use_globally)

    return init(historian, use_globally)


def init(historian: mincepy.Historian = None, use_globally=True) -> "pyos.Session":
    """Initialise a Historian such that it is ready to be used with pyOS"""
    global _GLOBAL_SESSION  # noqa: PLW0603
    historian = historian or mincepy.get_historian()

    db.schema.ensure_up_to_date(historian)

    # Create the global session
    session = _sessions.Session(historian)

    if use_globally:
        _GLOBAL_SESSION = session

    return session


def get_historian() -> mincepy.Historian:
    """Get the active historian in pyos"""
    if _GLOBAL_SESSION is None:
        raise RuntimeError(
            "A global pyOS session has not been initialised.  Call connect() or init() first."
        )

    return _GLOBAL_SESSION.historian


def get_global_session() -> "pyos.Session":
    return _GLOBAL_SESSION


def reset_global_session():
    global _GLOBAL_SESSION  # noqa: PLW0603
    if _GLOBAL_SESSION is not None:
        _GLOBAL_SESSION.close()
        _GLOBAL_SESSION = None
