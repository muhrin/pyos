"""Module containig standard option names"""

from . import opts

__all__ = 'l', 'L', 'p', 'd', 'u', 's', 'mindepth', 'maxdepth'

# pylint: disable=invalid-name

# region Options
l = opts.Option('l')
d = opts.Option('d')
p = opts.Option('p')
L = opts.Option('L')
s = opts.Option('s')
u = opts.Option('u')
maxdepth = opts.Option('maxdepth')
mindepth = opts.Option('mindepth')

# endregion
