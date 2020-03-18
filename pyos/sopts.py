"""Module containig standard option names"""

from . import opts

__all__ = 'l', 'L', 'd', 'mindepth', 'maxdepth'

# pylint: disable=invalid-name

# region Options
l = opts.Flag('l')
d = opts.Flag('d')
L = opts.ValueOp('L')
maxdepth = opts.ValueOp('maxdepth')
mindepth = opts.ValueOp('mindepth')

# endregion
