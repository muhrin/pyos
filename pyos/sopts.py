"""Module containig standard option names"""

from . import opts

__all__ = ('l', 'mindepth', 'maxdepth')

# region Options
l = opts.Flag('l')
maxdepth = opts.ValueOp('maxdepth')
mindepth = opts.ValueOp('mindepth')

# endregion
