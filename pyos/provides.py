"""This module is for entry points that extend PyOS' functionality"""

import pyos


def get_types():
    """Provide the list of types and helpers we define for mincepy"""
    return (pyos.pathlib.Path,)
