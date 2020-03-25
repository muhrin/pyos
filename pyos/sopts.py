"""Module containig standard option names"""

from . import opts

__all__ = 'l', 'L', 'n', 'p', 'd', 'u', 's'

# pylint: disable=invalid-name

# region Options
l = opts.Option('l')
n = opts.Option('n')
d = opts.Option('d')
p = opts.Option('p')
L = opts.Option('L')
s = opts.Option('s')
u = opts.Option('u')

# endregion
