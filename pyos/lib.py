import mincepy

from . import db

__all__ = 'init', 'reset'


def connect(uri: str = '') -> mincepy.Historian:
    return db.connect(uri)


def init() -> mincepy.Historian:
    return db.init()


def reset():
    db.reset()
