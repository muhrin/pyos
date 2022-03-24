# -*- coding: utf-8 -*-
import mincepy.testing

import pyos
from pyos.psh import cmds


def test_saving_path():
    path = pyos.pathlib.Path('/some/random/path/')
    path_str = str(path)
    obj_id = cmds.save(path)
    del path

    loaded = cmds.load(obj_id)
    assert str(loaded) == path_str


def test_parents_file():
    """Test that parents works for files"""
    path = pyos.pathlib.PurePath('tmp/test/sub/a')
    assert path.parents == [
        pyos.pathlib.Path('tmp/test/sub'),
        pyos.pathlib.Path('tmp/test'),
        pyos.pathlib.Path('tmp'),
        pyos.pathlib.Path('.')
    ]

    # Test absolute
    path = pyos.pathlib.Path('/tmp/test/sub/a')
    assert path.parents == [
        pyos.pathlib.Path('/tmp/test/sub'),
        pyos.pathlib.Path('/tmp/test'),
        pyos.pathlib.Path('/tmp'),
        pyos.pathlib.Path('/')
    ]


def test_parents_dir():
    """Test that parents works for directories"""
    path = pyos.pathlib.Path('tmp/test/sub/a/')
    assert path.parents == [
        pyos.pathlib.Path('tmp/test/sub/'),
        pyos.pathlib.Path('tmp/test/'),
        pyos.pathlib.Path('tmp/'),
        pyos.pathlib.Path('./')
    ]

    # Test absolute
    path = pyos.pathlib.Path('/tmp/test/sub/a')
    assert path.parents == [
        pyos.pathlib.Path('/tmp/test/sub/'),
        pyos.pathlib.Path('/tmp/test/'),
        pyos.pathlib.Path('/tmp/'),
        pyos.pathlib.Path('/')
    ]


def test_exists_object():
    car = mincepy.testing.Car()
    pyos.db.lib.save_one(car, 'my_car')

    assert pyos.pathlib.Path('my_car').exists()
    assert not pyos.pathlib.Path('not_my_car').exists()


def test_exists_path():
    car = mincepy.testing.Car()
    pyos.os.makedirs('folder/')
    pyos.db.lib.save_one(car, 'folder/my_car')

    assert pyos.pathlib.Path('folder/').exists()
    assert not pyos.pathlib.Path('other_folder/').exists()
