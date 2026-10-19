from . import cmds, completion, flags, shell
from .cmds import *
from .flags import *
from .shell import *

cwd = completion.PathCompletion(".")

_ADDITIONAL = "completion", "cwd"

__all__ = cmds.__all__ + flags.__all__ + shell.__all__ + _ADDITIONAL  # noqa: PLE0605
