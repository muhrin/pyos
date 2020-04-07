"""Print working directory command"""

import pyos


def pwd() -> pyos.pathlib.Path:
    """Return the current working directory"""
    return pyos.pathlib.Path().resolve()
