from mincepy.testing import Car

import pyos
from pyos import psh


def test_mv_basic():
    car = Car()
    car.save()

    # Move to test subdirectory
    psh.mv(car, 'test/')

    assert psh.locate(car) == psh.pwd() / 'test/' / str(car.obj_id)

    contents = psh.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id

    # Now move test into a subfolder
    psh.mv('test/', 'sub/')
    contents = psh.ls()
    assert len(contents) == 1
    assert contents[0].name == 'sub/'

    contents = psh.ls('sub/')
    assert len(contents) == 1
    assert contents[0].name == 'test/'


def test_mv_from_str():
    car = Car()
    car.save()

    psh.mv(str(car.obj_id), 'test/')
    contents = psh.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_from_path():
    car = Car()
    car.save()

    psh.mv(psh.locate(car), 'test/')
    contents = psh.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_from_obj_id():
    car = Car()
    car.save()

    psh.mv(car.obj_id, 'test/')
    contents = psh.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_dest_as_path():
    car = Car()
    car.save()

    psh.mv(car.obj_id, pyos.pathlib.Path('test/'))
    contents = psh.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_remote():
    """Test moving an object from one remote path to another"""
    car = Car()
    psh.save(car, '/test/path_a/')
    psh.mv(car, '/a/different/path/')

    contents = psh.ls('/a/different/path/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_overwrite():
    """Test the moving handles overwriting an existing name correctly"""
    car1 = Car()
    psh.save(car1, 'my_car')

    car2 = Car()
    car2.save()
    psh.mv(car2, 'my_car')


def test_mv_no_clobber():
    """Test moving with no clobber"""
    car1 = Car()
    psh.save(car1, 'my_car')

    car2 = Car()
    psh.save(car2, 'my_car2')

    assert len(psh.ls()) == 2
    psh.mv(-psh.n, car2, 'my_car')
    assert len(psh.ls()) == 2  # Still 2


def test_mv_multiple():
    ferrari = Car()
    psh.save(ferrari, 'ferrari')
    skoda = Car()
    psh.save(skoda, 'skoda')

    assert len(psh.ls()) == 2

    psh.mv('skoda', 'ferrari', 'garage/')
    assert psh.ls('garage/') | len == 2
