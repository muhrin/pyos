from mincepy.testing import Car

import pyos
from pyos import cmd


def test_mv_basic():
    car = Car()
    car.save()

    # Move to test subdirectory
    cmd.mv(car, 'test/')

    assert cmd.locate(car)[0].abspath == cmd.pwd() / 'test/' / str(car.obj_id)

    contents = cmd.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id

    # Now move test into a subfolder
    cmd.mv('test/', 'sub/')
    contents = cmd.ls()
    assert len(contents) == 1
    assert contents[0].name == 'sub/'

    contents = cmd.ls('sub/')
    assert len(contents) == 1
    assert contents[0].name == 'test/'


def test_mv_from_str():
    car = Car()
    car.save()

    cmd.mv(str(car.obj_id), 'test/')
    contents = cmd.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_from_path():
    car = Car()
    car.save()

    cmd.mv(cmd.locate(car), 'test/')
    contents = cmd.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_from_obj_id():
    car = Car()
    car.save()

    cmd.mv(car.obj_id, 'test/')
    contents = cmd.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_dest_as_path():
    car = Car()
    car.save()

    cmd.mv(car.obj_id, pyos.PyosPath('test/'))
    contents = cmd.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_remote():
    """Test moving an object from one remote path to another"""
    car = Car()
    cmd.save(car, '/test/path_a/')
    cmd.mv(car, '/a/different/path/')

    contents = cmd.ls('/a/different/path/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_overwrite():
    """Test the moving handles overwriting an existing name correctly"""
    car1 = Car()
    cmd.save(car1, 'my_car')

    car2 = Car()
    car2.save()
    cmd.mv(car2, 'my_car')


def test_mv_no_clobber():
    """Test moving with no clobber"""
    car1 = Car()
    cmd.save(car1, 'my_car')

    car2 = Car()
    cmd.save(car2, 'my_car2')

    assert len(cmd.ls()) == 2
    cmd.mv(-cmd.n, car2, 'my_car')
    assert len(cmd.ls()) == 2  # Still 2
