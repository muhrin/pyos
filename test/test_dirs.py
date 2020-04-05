from mincepy.testing import Person

import pyos
from pyos import cmds


def test_working_path():
    home = cmds.pwd()
    address_book = pyos.PyosPath('address_book/').resolve()
    with pyos.working_path(address_book):
        person_id = Person('martin', 34).save()
        assert cmds.pwd() == home / address_book

    contents = cmds.ls()
    assert len(contents) == 1
    assert contents[0].abspath == address_book

    contents = cmds.ls(address_book)
    assert len(contents) == 1
    assert contents[0].obj_id == person_id
