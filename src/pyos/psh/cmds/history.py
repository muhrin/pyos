"""The history command"""

import mincepy

from . import cat
from ... import _globals, psh_lib


@psh_lib.command()
def history(obj):
    hist: mincepy.Historian = _globals.get_global_session().historian
    for entry in hist.history(obj):
        cat.cat(entry.obj)
