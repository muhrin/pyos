# -*- coding: utf-8 -*-
from mincepy.testing import Car

import pyos
from pyos import psh
from pyos import pathlib


def test_root():
    """Make sure that root is represented as '/' always"""
    assert str(pathlib.PurePath('/')) == '/'
    assert str(pathlib.PurePath('//').resolve()) == '/'


def test_iterdir():
    psh.save(Car(), 'my_car')
    with pathlib.working_path('sub/'):
        psh.save(Car(), 'my_sub_car')
    cwd = pathlib.Path()

    content = tuple(map(pathlib.Path.name.fget, cwd.iterdir()))
    assert len(content) == 2

    assert 'my_car' in content
    assert 'sub/' in content


def test_resolve_parent_dir():
    expected_result = pathlib.PurePath('a/')
    assert pathlib.PurePath('a/b/') / pathlib.PurePath('../') == expected_result
    assert pathlib.PurePath('a/b/') / pathlib.PurePath('..') == expected_result


def test_resolve_current_dir():
    expected_result = pathlib.PurePath('a/b/')
    assert pathlib.PurePath('a/b/') / pathlib.PurePath('./') == expected_result
    assert pathlib.PurePath('a/b/') / pathlib.PurePath('.') == expected_result


def test_path_joining():
    # Check that we can join with a file path and it will be promoted to a directory
    result = pathlib.PurePath('/home') / pathlib.PurePath('martin')
    assert pyos.os.fspath(result) == '/home/martin'
