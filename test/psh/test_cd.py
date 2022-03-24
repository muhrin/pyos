# -*- coding: utf-8 -*-
"""Tests for the change directory command"""

import pyos
import pyos.os
from pyos import psh

# pylint: disable=invalid-name


def test_cd_simple():
    pyos.os.makedirs('a/b/')

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


def test_cd_minus(pyos_shell):
    """Test changing back to last directory using 'cd -'"""
    pyos.os.makedirs('/some/random/dir/')
    start_dir = pyos.os.getcwd()
    pyos_shell.app_cmd('cd /some/random/dir/')
    assert pyos.os.getcwd() == '/some/random/dir'
    pyos_shell.app_cmd('cd -')
    assert pyos.os.getcwd() == start_dir


def test_cd_home(pyos_shell):
    home_dir = pyos.db.homedir()
    rand_dir = '/some/rand/dir'
    pyos.os.makedirs(rand_dir)
    pyos.os.makedirs(home_dir)

    pyos.os.chdir(rand_dir)
    pyos_shell.app_cmd('cd ~')

    assert pyos.os.getcwd() == home_dir

    pyos.os.chdir(rand_dir)
    pyos_shell.app_cmd('cd ~/')
    assert pyos.os.getcwd() == home_dir
