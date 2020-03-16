"""Module containig standard option names"""

from . import opts

__all__ = ('l', 'mindepth', 'maxdepth')

# region Options
l = opts.Op('minus_l')
maxdepth = opts.Op('maxdepth')
mindepth = opts.Op('mindepth')

# endregion
