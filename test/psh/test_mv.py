import io

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
    """Test that mv overwrites an existing object correctly"""
    car1 = Car()
    psh.save(car1, 'my_car')

    car2 = Car()
    car2.save()
    psh.mv(psh.f, car2, 'my_car')


def test_mv_overwrite_prompt(monkeypatch):
    """Test moving with that would cause an overwrite without force"""
    car1 = Car()
    psh.save(car1, 'my_car')

    car2 = Car()
    psh.save(car2, 'my_car2')

    assert len(psh.ls()) == 2

    # This will prompt
    confirm = io.StringIO('N')
    monkeypatch.setattr('sys.stdin', confirm)
    psh.mv(car2, 'my_car')
    assert len(psh.ls()) == 2  # Still 2

    # Now overwrite
    confirm = io.StringIO('Y')
    monkeypatch.setattr('sys.stdin', confirm)
    psh.mv(car2, 'my_car')
    assert len(psh.ls()) == 1


def test_mv_multiple():
    ferrari = Car()
    psh.save(ferrari, 'ferrari')
    skoda = Car()
    psh.save(skoda, 'skoda')

    assert len(psh.ls()) == 2

    psh.mv('skoda', 'ferrari', 'garage/')
    assert psh.ls('garage/') | len == 2


def test_mv_rename_directory():
    psh.cd('cars/')
    car_id = Car().save()
    psh.cd('../')

    # Now, rename the directory using mv
    psh.mv('cars/', 'new_cars')
    results = psh.ls('new_cars/')

    assert len(results) == 1
    assert results[0].obj_id == car_id
