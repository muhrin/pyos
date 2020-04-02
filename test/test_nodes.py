"""Tests for pyos nodes"""
import pytest

import mincepy
from mincepy.testing import Person

import pyos
import pyos.nodes


def test_obj_in_directory():
    home = pyos.pyos.pwd()
    address_book = pyos.PyosPath('address_book/').resolve()
    with pyos.working_path(address_book):
        person_id = pyos.lib.save_one(Person('martin', 34), 'martin')
        assert pyos.pyos.pwd() == home / address_book

    home_node = pyos.nodes.DirectoryNode(home)
    home_node.expand(depth=-1)
    assert pyos.PyosPath('address_book/martin') in home_node

    dir_node = pyos.nodes.DirectoryNode(address_book)
    dir_node.expand()

    assert person_id in dir_node


def test_dir_in_directory():
    home = pyos.pyos.pwd()
    address_book = pyos.PyosPath('address_book/').resolve()
    with pyos.working_path(address_book):
        person_id = pyos.pyos.save(Person('martin', 34), 'martin')

    home_node = pyos.nodes.DirectoryNode(home)
    home_node.expand(depth=-1)

    assert pyos.PyosPath('address_book/') in home_node
    assert pyos.PyosPath('address_book/martin') in home_node

    address_book_node = pyos.nodes.DirectoryNode(home_node.abspath / 'address_book/')
    address_book_node.expand(1)  # Have to expand so it finds internal objects
    assert person_id in address_book_node


def test_dir_delete(historian: mincepy.Historian):
    """Test deleting directory (and all contents)"""
    address_book = pyos.PyosPath('address_book/').resolve()
    with pyos.working_path(address_book):
        martin_id = pyos.pyos.save(Person('martin', 34), 'martin')
        sonia_id = pyos.pyos.save(Person('sonia', 31), 'sub/sonia')

    address_book_node = pyos.nodes.DirectoryNode(address_book)
    assert address_book.exists()
    address_book_node.delete()
    assert not address_book.exists()

    with pytest.raises(mincepy.ObjectDeleted):
        historian.load(martin_id)
    with pytest.raises(mincepy.ObjectDeleted):
        historian.load(sonia_id)
