from mincepy.testing import Person

import pyos
from pyos import psh


def test_working_path():
    home = psh.pwd()
    address_book = pyos.PyosPath('address_book/').resolve()
    with pyos.fs.working_path(address_book):
        person_id = Person('martin', 34).save()
        assert psh.pwd() == home / address_book

    contents = psh.ls()
    assert len(contents) == 1
    assert contents[0].abspath == address_book

    contents = psh.ls(address_book)
    assert len(contents) == 1
    assert contents[0].obj_id == person_id
