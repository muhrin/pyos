"""Print working directory command"""

import pyos


@pyos.psh_lib.command()
def pwd() -> pyos.pathlib.Path:
    """Return the current working directory"""
    return pyos.pathlib.Path().resolve()
