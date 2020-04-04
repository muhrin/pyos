"""Print working directory command"""

import pyos.dirs


def pwd():
    """Return the current working directory"""
    return pyos.dirs.cwd()
