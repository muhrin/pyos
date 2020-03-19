from mincepy.testing import Person

import pyos


def test_working_path():
    home = pyos.pyos.pwd()
    address_book = pyos.PyosPath('address_book/').resolve()
    with pyos.working_path(address_book):
        person_id = Person('martin', 34).save()
        assert pyos.pyos.pwd() == home / address_book

    contents = pyos.pyos.ls()
    assert len(contents) == 1
    assert contents[0].abspath == address_book

    contents = pyos.pyos.ls(address_book)
    assert len(contents) == 1
    assert contents[0].obj_id == person_id
