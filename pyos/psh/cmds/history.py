"""The history command"""

import pyos
from .cat import cat


def history(obj):
    hist = pyos.db.get_historian()
    for entry in hist.history(obj):
        cat(entry.obj)
