import mincepy.testing

from pyos import pyos
from pyos import dirs


def test_reaching_root():
    """Assert the correct behaviour when traversing up until reaching root and beyond"""
    cwd = dirs.cwd()
    for _ in range(len(cwd.parts) - 1):
        pyos.cd('..')

    # Should be at root
    assert dirs.cwd() == dirs.PyosPath('/')

    # Now trying going up again
    pyos.cd('..')
    # Should still be at root
    assert dirs.cwd() == dirs.PyosPath('/')


def test_saving_path():
    path = dirs.PyosPath('/some/random/path/')
    path_str = str(path)
    obj_id = pyos.save(path)
    del path

    loaded = pyos.load(obj_id)
    assert str(loaded) == path_str


def test_parents_file():
    """Test that parents works for files"""
    path = dirs.PyosPath('tmp/test/sub/a')
    assert path.parents == [
        pyos.PyosPath('tmp/test/sub/'),
        pyos.PyosPath('tmp/test/'),
        pyos.PyosPath('tmp/'),
        pyos.PyosPath('./')
    ]

    # Test absolute
    path = dirs.PyosPath('/tmp/test/sub/a')
    assert path.parents == [
        pyos.PyosPath('/tmp/test/sub/'),
        pyos.PyosPath('/tmp/test/'),
        pyos.PyosPath('/tmp/'),
        pyos.PyosPath('/')
    ]


def test_parents_dir():
    """Test that parents works for directories"""
    path = dirs.PyosPath('tmp/test/sub/a/')
    assert path.parents == [
        pyos.PyosPath('tmp/test/sub/'),
        pyos.PyosPath('tmp/test/'),
        pyos.PyosPath('tmp/'),
        pyos.PyosPath('./')
    ]

    # Test absolute
    path = dirs.PyosPath('/tmp/test/sub/a')
    assert path.parents == [
        pyos.PyosPath('/tmp/test/sub/'),
        pyos.PyosPath('/tmp/test/'),
        pyos.PyosPath('/tmp/'),
        pyos.PyosPath('/')
    ]


def test_exists_object():
    car = mincepy.testing.Car()
    pyos.lib.save_one(car, 'my_car')

    assert dirs.PyosPath('my_car').exists()
    assert not dirs.PyosPath('not_my_car').exists()


def test_exists_path():
    car = mincepy.testing.Car()
    pyos.lib.save_one(car, 'folder/my_car')

    assert dirs.PyosPath('folder/').exists()
    assert not dirs.PyosPath('other_folder/').exists()
