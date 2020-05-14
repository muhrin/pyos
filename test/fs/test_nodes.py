"""Tests for pyos nodes"""
from mincepy.testing import Person

import pyos
from pyos import psh


def test_obj_in_directory():
    home = psh.pwd()
    address_book = pyos.pathlib.Path('address_book/').resolve()
    with pyos.pathlib.working_path(address_book):
        person_id = pyos.db.save_one(Person('martin', 34), 'martin')
        assert psh.pwd() == home / address_book

    home_node = pyos.fs.DirectoryNode(home)
    home_node.expand(depth=-1)
    assert len(home_node) == 1
    assert pyos.pathlib.Path('address_book/martin') in home_node

    dir_node = pyos.fs.DirectoryNode(address_book)
    dir_node.expand()

    assert person_id in dir_node
