"""Module containig flags"""

from pyos import psh_lib

__all__ = 'f', 'l', 'L', 'n', 'p', 'd', 'u', 's'

# pylint: disable=invalid-name

# Define standard flags
d = psh_lib.Option('d')
f = psh_lib.Option('f')
l = psh_lib.Option('l')
L = psh_lib.Option('L')
n = psh_lib.Option('n')
p = psh_lib.Option('p')
s = psh_lib.Option('s')
u = psh_lib.Option('u')
