"""Tests for the change directory command"""

import pyos
from pyos import psh


def test_cd_simple():
    start = psh.pwd()
    assert isinstance(start, pyos.pathlib.Path)

    # Try relative directory changes
    a = 'a/'
    psh.cd(a)
    assert psh.pwd() == start / a

    b = 'b/'
    psh.cd(b)
    assert psh.pwd() == start / a / b

    # Try absolute directory change
    psh.cd(start / a)
    assert psh.pwd() == start / a

    # Try .. change
    psh.cd('..')
    assert psh.pwd() == start


def test_reaching_root():
    """Assert the correct behaviour when traversing up until reaching root and beyond"""
    cwd = psh.pwd()
    for _ in range(len(cwd.parts) - 1):
        psh.cd('../..')

    # Should be at root
    assert psh.pwd() == pyos.pathlib.Path('/')

    # Now trying going up again
    psh.cd('../..')
    # Should still be at root
    assert psh.pwd() == pyos.pathlib.Path('/')
