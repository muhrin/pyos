"""Module containig standard option names"""

from . import opts

__all__ = 'l', 'L', 'p', 'd', 'mindepth', 'maxdepth'

# pylint: disable=invalid-name

# region Options
l = opts.Option('l')
d = opts.Option('d')
p = opts.Option('p')
L = opts.Option('L')
maxdepth = opts.Option('maxdepth')
mindepth = opts.Option('mindepth')

# endregion
