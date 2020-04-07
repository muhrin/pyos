from . import db

__all__ = 'init', 'reset'


def init():
    db.init()


def reset():
    db.reset()
