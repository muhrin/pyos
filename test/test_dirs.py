from mincepy.testing import Person

import pyos
from pyos import cmd


def test_working_path():
    home = cmd.pwd()
    address_book = pyos.PyosPath('address_book/').resolve()
    with pyos.working_path(address_book):
        person_id = Person('martin', 34).save()
        assert cmd.pwd() == home / address_book

    contents = cmd.ls()
    assert len(contents) == 1
    assert contents[0].abspath == address_book

    contents = cmd.ls(address_book)
    assert len(contents) == 1
    assert contents[0].obj_id == person_id
