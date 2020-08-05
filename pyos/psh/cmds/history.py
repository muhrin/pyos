"""The history command"""

import pyos
from pyos import db
from .cat import cat


@pyos.psh_lib.command()
def history(obj):
    hist = db.get_historian()
    for entry in hist.history(obj):
        cat(entry.obj)
