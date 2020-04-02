"""Module containig standard option names"""

from . import opts

__all__ = 'f', 'l', 'L', 'n', 'p', 'd', 'u', 's'

# pylint: disable=invalid-name

# region Options
d = opts.Option('d')
f = opts.Option('f')
l = opts.Option('l')
L = opts.Option('L')
n = opts.Option('n')
p = opts.Option('p')
s = opts.Option('s')
u = opts.Option('u')

# endregion
