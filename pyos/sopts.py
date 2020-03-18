"""Module containig standard option names"""

from . import opts

__all__ = 'l', 'd', 'mindepth', 'maxdepth'

# pylint: disable=invalid-name

# region Options
l = opts.Flag('l')
d = opts.Flag('d')
maxdepth = opts.ValueOp('maxdepth')
mindepth = opts.ValueOp('mindepth')

# endregion
