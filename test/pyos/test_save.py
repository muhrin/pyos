import pytest

import mincepy
from mincepy.testing import Car

from pyos import pyos


def test_save():
    car = Car()
    obj_id = pyos.save(car)
    assert obj_id == car.obj_id


def test_save_with_name():
    car = Car()
    pyos.save(car, 'my_car')
    results = pyos.ls('my_car')
    assert len(results) == 1
    assert results[0].name == 'my_car'


def test_save_to_dir():
    for _ in range(10):
        pyos.save(Car(), 'test/')

    results = pyos.ls('test/')
    assert len(results) == 10

    # Now check that save will promote a file to a directory
    pyos.save(Car(), 'test')
    assert len(pyos.ls('test/')) == 10


def test_save_same_name():
    car = Car()
    car_id = pyos.save(car, 'my_car')
    car2 = Car()
    with pytest.raises(mincepy.DuplicateKeyError):
        # For now this raises but this may change in the future
        pyos.save(car2, 'my_car')

    # Now test the force flags
    car2_id = pyos.save(-pyos.f, car2, 'my_car')
    assert car_id != car2_id
