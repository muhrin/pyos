# -*- coding: utf-8 -*-
"""Tests for pyos directory nodes"""
import pytest

import mincepy
from mincepy.testing import Person

import pyos
from pyos import psh

# pylint: disable=unused-argument


def test_dir_in_directory():
    home = psh.pwd()
    address_book = pyos.pathlib.Path('address_book/').resolve()
    pyos.os.makedirs(address_book)
    with pyos.pathlib.working_path(address_book):
        person_id = psh.save(Person('martin', 34), 'martin')

    home_node = pyos.fs.DirectoryNode(home)
    home_node.expand(depth=-1)

    assert pyos.pathlib.Path('address_book/') in home_node
    assert pyos.pathlib.Path('address_book/martin') in home_node

    address_book_node = pyos.fs.DirectoryNode(home_node.abspath / 'address_book/')
    address_book_node.expand(1)  # Have to expand so it finds internal objects
    assert person_id in address_book_node


def test_dir_delete(historian: mincepy.Historian):
    """Test deleting directory (and all contents)"""
    address_book = pyos.pathlib.Path('address_book/').resolve()
    pyos.os.makedirs('address_book/sub/')
    with pyos.pathlib.working_path(address_book):
        martin_id = psh.save(Person('martin', 34), 'martin')
        sonia_id = psh.save(Person('sonia', 31), 'sub/sonia')

    address_book_node = pyos.fs.DirectoryNode(address_book)
    assert address_book.exists()
    address_book_node.delete()
    assert not address_book.exists()

    with pytest.raises(mincepy.NotFound):
        historian.load(martin_id)
    with pytest.raises(mincepy.NotFound):
        historian.load(sonia_id)


def test_move_dir(historian: mincepy.Historian):
    """Test moving a directory node"""
    pyos.os.makedirs('address_book/')
    pyos.os.makedirs('sub/')

    path = pyos.pathlib.Path('address_book/').resolve()
    with pyos.pathlib.working_path(path):
        martin_id = psh.save(Person('martin', 34), 'martin')

    node = pyos.fs.DirectoryNode(path)
    node.move('sub/')

    assert node.abspath == pyos.Path('sub/address_book/').resolve()
    node.expand(1)
    assert node.children[0].obj_id == martin_id


def test_rename_dir(historian: mincepy.Historian):
    """Test renaming a directory node"""
    path = pyos.pathlib.Path('address_book/').resolve()
    pyos.os.makedirs(path)
    with pyos.pathlib.working_path(path):
        martin_id = psh.save(Person('martin', 34), 'martin')

    node = pyos.fs.DirectoryNode(path)
    node.rename('abook')

    assert node.abspath == pyos.Path('abook/').resolve()
    node.expand(1)
    assert node.children[0].obj_id == martin_id
