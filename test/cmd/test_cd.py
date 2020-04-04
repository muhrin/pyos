"""Tests for the change directory command"""

import pyos
from pyos import cmd


def test_cd_simple():
    start = cmd.pwd()
    assert isinstance(start, pyos.PyosPath)

    # Try relative directory changes
    a = 'a/'
    cmd.cd(a)
    assert cmd.pwd() == start / a

    b = 'b/'
    cmd.cd(b)
    assert cmd.pwd() == start / a / b

    # Try absolute directory change
    cmd.cd(start / a)
    assert cmd.pwd() == start / a

    # Try .. change
    cmd.cd('..')
    assert cmd.pwd() == start
