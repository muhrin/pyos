from mincepy.testing import Person

import pyos
from pyos import pysh


def test_working_path():
    home = pysh.pwd()
    address_book = pyos.PyosPath('address_book/').resolve()
    with pyos.fs.working_path(address_book):
        person_id = Person('martin', 34).save()
        assert pysh.pwd() == home / address_book

    contents = pysh.ls()
    assert len(contents) == 1
    assert contents[0].abspath == address_book

    contents = pysh.ls(address_book)
    assert len(contents) == 1
    assert contents[0].obj_id == person_id
