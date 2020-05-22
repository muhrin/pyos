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


def test_results_slicing():
    num_persons = 10

    for _ in range(num_persons):
        Person('test', 30).save()

    cwd = pyos.fs.DirectoryNode('./')
    cwd.expand()
    assert len(cwd) == num_persons

    # Now try slicing it
    first_n = cwd[:5]
    assert len(first_n) == 5
    assert isinstance(first_n, pyos.fs.ResultsNode)

    # Now slice the results
    first_n.show('creator', 'name', 'ctime', mode=pyos.fs.TABLE_VIEW)
    first_2 = first_n[:2]
    assert len(first_2) == 2
    assert isinstance(first_n, pyos.fs.ResultsNode)
    # Now make sure the view modes were copied
    assert first_2.view_mode == first_n.view_mode
    assert first_2.showing == first_n.showing
