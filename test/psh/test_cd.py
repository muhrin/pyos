"""Tests for the change directory command"""

import pyos
from pyos.psh import cmds


def test_cd_simple():
    start = cmds.pwd()
    assert isinstance(start, pyos.PyosPath)

    # Try relative directory changes
    a = 'a/'
    cmds.cd(a)
    assert cmds.pwd() == start / a

    b = 'b/'
    cmds.cd(b)
    assert cmds.pwd() == start / a / b

    # Try absolute directory change
    cmds.cd(start / a)
    assert cmds.pwd() == start / a

    # Try .. change
    cmds.cd('..')
    assert cmds.pwd() == start
