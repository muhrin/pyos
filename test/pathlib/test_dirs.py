# -*- coding: utf-8 -*-
from mincepy.testing import Person

import pyos
import pyos.os
from pyos.fs import nodes
from pyos import psh


def test_working_path():
    # pylint: disable=no-value-for-parameter
    home = psh.pwd()
    address_book = pyos.pathlib.Path('address_book/').resolve()
    pyos.os.makedirs(address_book)
    with pyos.pathlib.working_path(address_book):
        person_id = Person('martin', 34).save()
        assert psh.pwd() == home / address_book

    contents = psh.ls()
    assert len(contents) == 1
    assert isinstance(contents[0], nodes.FilesystemNode)
    assert contents[0].abspath == address_book  # pylint: disable=no-member

    contents = psh.ls(address_book)
    assert len(contents) == 1
    assert isinstance(contents[0], nodes.FilesystemNode)
    assert contents[0].entry_id == person_id  # pylint: disable=no-member
