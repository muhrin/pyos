"""Module containig flags"""

from pyos import shell

__all__ = 'f', 'l', 'L', 'n', 'p', 'd', 'u', 's'

# pylint: disable=invalid-name

# Define standard flags
d = shell.Option('d')
f = shell.Option('f')
l = shell.Option('l')
L = shell.Option('L')
n = shell.Option('n')
p = shell.Option('p')
s = shell.Option('s')
u = shell.Option('u')
