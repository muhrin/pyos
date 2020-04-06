"""Print working directory command"""

import pyos.fs


def pwd() -> pyos.fs.PyosPath:
    """Return the current working directory"""
    return pyos.fs.cwd()
