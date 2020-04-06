import mincepy.testing

import pyos
from pyos.psh import cmds


def test_saving_path():
    path = pyos.PyosPath('/some/random/path/')
    path_str = str(path)
    obj_id = cmds.save(path)
    del path

    loaded = cmds.load(obj_id)
    assert str(loaded) == path_str


def test_parents_file():
    """Test that parents works for files"""
    path = pyos.PyosPath('tmp/test/sub/a')
    assert path.parents == [
        pyos.PyosPath('tmp/test/sub/'),
        pyos.PyosPath('tmp/test/'),
        pyos.PyosPath('tmp/'),
        pyos.PyosPath('./')
    ]

    # Test absolute
    path = pyos.PyosPath('/tmp/test/sub/a')
    assert path.parents == [
        pyos.PyosPath('/tmp/test/sub/'),
        pyos.PyosPath('/tmp/test/'),
        pyos.PyosPath('/tmp/'),
        pyos.PyosPath('/')
    ]


def test_parents_dir():
    """Test that parents works for directories"""
    path = pyos.PyosPath('tmp/test/sub/a/')
    assert path.parents == [
        pyos.PyosPath('tmp/test/sub/'),
        pyos.PyosPath('tmp/test/'),
        pyos.PyosPath('tmp/'),
        pyos.PyosPath('./')
    ]

    # Test absolute
    path = pyos.PyosPath('/tmp/test/sub/a')
    assert path.parents == [
        pyos.PyosPath('/tmp/test/sub/'),
        pyos.PyosPath('/tmp/test/'),
        pyos.PyosPath('/tmp/'),
        pyos.PyosPath('/')
    ]


def test_exists_object():
    car = mincepy.testing.Car()
    pyos.db.lib.save_one(car, 'my_car')

    assert pyos.PyosPath('my_car').exists()
    assert not pyos.PyosPath('not_my_car').exists()


def test_exists_path():
    car = mincepy.testing.Car()
    pyos.db.lib.save_one(car, 'folder/my_car')

    assert pyos.PyosPath('folder/').exists()
    assert not pyos.PyosPath('other_folder/').exists()
