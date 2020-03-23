"""Tests for the change directory command"""

from pyos import pyos


def test_cd_simple():
    start = pyos.pwd()
    assert isinstance(start, pyos.PyosPath)

    # Try relative directory changes
    a = 'a/'
    pyos.cd(a)
    assert pyos.pwd() == start / a

    b = 'b/'
    pyos.cd(b)
    assert pyos.pwd() == start / a / b

    # Try absolute directory change
    pyos.cd(start / a)
    assert pyos.pwd() == start / a

    # Try .. change
    pyos.cd('..')
    assert pyos.pwd() == start
