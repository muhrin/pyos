"""The history command"""

import mincepy

from .cat import cat


def history(obj):
    hist = mincepy.get_historian()
    for entry in hist.history(obj):
        cat(entry.obj)
