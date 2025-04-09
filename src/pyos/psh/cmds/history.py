"""The history command"""

from . import cat
from ... import db, psh_lib


@psh_lib.command()
def history(obj):
    hist = db.get_historian()
    for entry in hist.history(obj):
        cat.cat(entry.obj)
