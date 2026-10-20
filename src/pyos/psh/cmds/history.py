"""The history command"""

import mincepy

from ... import _globals, fs, pathlib, psh_lib
from .. import flags
from .cat import cat
from .ls import ls


@psh_lib.command()
def history(obj, representer=None):
    """Show the saved versions of an object (oldest first).  The object can also be given as its
    id or path.  The representer is used to show each version, as for cat."""
    hist: mincepy.Historian = _globals.get_global_session().historian
    if isinstance(obj, (str, pathlib.PurePath, fs.BaseNode)):
        (node,) = ls(-flags.d, obj)
        if not isinstance(node, fs.ObjectNode):
            raise ValueError(f"history: '{obj}' is not an object")
        obj = node.obj_id

    return cat(*(entry.obj for entry in hist.history(obj)), representer=representer)
