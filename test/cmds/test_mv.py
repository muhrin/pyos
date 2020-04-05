from mincepy.testing import Car

import pyos
from pyos import cmds


def test_mv_basic():
    car = Car()
    car.save()

    # Move to test subdirectory
    cmds.mv(car, 'test/')

    assert cmds.locate(car)[0].abspath == cmds.pwd() / 'test/' / str(car.obj_id)

    contents = cmds.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id

    # Now move test into a subfolder
    cmds.mv('test/', 'sub/')
    contents = cmds.ls()
    assert len(contents) == 1
    assert contents[0].name == 'sub/'

    contents = cmds.ls('sub/')
    assert len(contents) == 1
    assert contents[0].name == 'test/'


def test_mv_from_str():
    car = Car()
    car.save()

    cmds.mv(str(car.obj_id), 'test/')
    contents = cmds.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_from_path():
    car = Car()
    car.save()

    cmds.mv(cmds.locate(car), 'test/')
    contents = cmds.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_from_obj_id():
    car = Car()
    car.save()

    cmds.mv(car.obj_id, 'test/')
    contents = cmds.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_dest_as_path():
    car = Car()
    car.save()

    cmds.mv(car.obj_id, pyos.PyosPath('test/'))
    contents = cmds.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_remote():
    """Test moving an object from one remote path to another"""
    car = Car()
    cmds.save(car, '/test/path_a/')
    cmds.mv(car, '/a/different/path/')

    contents = cmds.ls('/a/different/path/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_overwrite():
    """Test the moving handles overwriting an existing name correctly"""
    car1 = Car()
    cmds.save(car1, 'my_car')

    car2 = Car()
    car2.save()
    cmds.mv(car2, 'my_car')


def test_mv_no_clobber():
    """Test moving with no clobber"""
    car1 = Car()
    cmds.save(car1, 'my_car')

    car2 = Car()
    cmds.save(car2, 'my_car2')

    assert len(cmds.ls()) == 2
    cmds.mv(-cmds.n, car2, 'my_car')
    assert len(cmds.ls()) == 2  # Still 2
