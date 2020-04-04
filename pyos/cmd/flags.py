"""Module containig flags"""

import pyos

__all__ = 'f', 'l', 'L', 'n', 'p', 'd', 'u', 's'

# pylint: disable=invalid-name

# region Options
d = pyos.opts.Option('d')
f = pyos.opts.Option('f')
l = pyos.opts.Option('l')
L = pyos.opts.Option('L')
n = pyos.opts.Option('n')
p = pyos.opts.Option('p')
s = pyos.opts.Option('s')
u = pyos.opts.Option('u')

# endregion
