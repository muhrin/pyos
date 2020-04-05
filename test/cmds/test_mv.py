from mincepy.testing import Car

import pyos
from pyos import pysh


def test_mv_basic():
    car = Car()
    car.save()

    # Move to test subdirectory
    pysh.mv(car, 'test/')

    assert pysh.locate(car)[0].abspath == pysh.pwd() / 'test/' / str(car.obj_id)

    contents = pysh.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id

    # Now move test into a subfolder
    pysh.mv('test/', 'sub/')
    contents = pysh.ls()
    assert len(contents) == 1
    assert contents[0].name == 'sub/'

    contents = pysh.ls('sub/')
    assert len(contents) == 1
    assert contents[0].name == 'test/'


def test_mv_from_str():
    car = Car()
    car.save()

    pysh.mv(str(car.obj_id), 'test/')
    contents = pysh.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_from_path():
    car = Car()
    car.save()

    pysh.mv(pysh.locate(car), 'test/')
    contents = pysh.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_from_obj_id():
    car = Car()
    car.save()

    pysh.mv(car.obj_id, 'test/')
    contents = pysh.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_dest_as_path():
    car = Car()
    car.save()

    pysh.mv(car.obj_id, pyos.PyosPath('test/'))
    contents = pysh.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_remote():
    """Test moving an object from one remote path to another"""
    car = Car()
    pysh.save(car, '/test/path_a/')
    pysh.mv(car, '/a/different/path/')

    contents = pysh.ls('/a/different/path/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_overwrite():
    """Test the moving handles overwriting an existing name correctly"""
    car1 = Car()
    pysh.save(car1, 'my_car')

    car2 = Car()
    car2.save()
    pysh.mv(car2, 'my_car')


def test_mv_no_clobber():
    """Test moving with no clobber"""
    car1 = Car()
    pysh.save(car1, 'my_car')

    car2 = Car()
    pysh.save(car2, 'my_car2')

    assert len(pysh.ls()) == 2
    pysh.mv(-pysh.n, car2, 'my_car')
    assert len(pysh.ls()) == 2  # Still 2
