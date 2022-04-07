# -*- coding: utf-8 -*-
import pytest

import pyos.os
from pyos import psh

# pylint: disable=no-value-for-parameter


def test_mkdir_basic():
    """Delete by the various identifier"""
    # Try with and without trailing slash
    psh.mkdir('test/')
    assert pyos.os.isdir('test/')

    psh.mkdir('test2')
    assert pyos.os.isdir('test2')

    psh.mkdir(-psh.p, 'test/subtest/subsubtest')
    assert pyos.os.isdir('test/subtest/subsubtest')

    # Test creating existing
    with pytest.raises(pyos.exceptions.FileExistsError):
        psh.mkdir('test/')

    # With -p flag should be OK
    psh.mkdir(-psh.p, 'test/')


def test_mkdir_cmd(pyos_shell):
    """Test the mkdir REPL command"""
    pyos_shell.app_cmd('mkdir test/')
    assert pyos.os.isdir('test/')

    pyos_shell.app_cmd('mkdir test2')
    assert pyos.os.isdir('test2')

    pyos_shell.app_cmd('mkdir -p test/subtest/subsubtest')
    assert pyos.os.isdir('test/subtest/subsubtest')

    # Test creating existing
    with pytest.raises(pyos.exceptions.FileExistsError):
        pyos_shell.app_cmd('mkdir test/')

    # With -p flag should be OK
    pyos_shell.app_cmd('mkdir -p test/')
