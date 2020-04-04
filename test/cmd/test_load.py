from mincepy.testing import Car

import pyos
from pyos import cmd


def test_load_single():
    """Test loading a single objects just returns that object and not a list"""
    car = Car()
    car_id = car.save()
    loaded = cmd.load(car_id)
    assert loaded is car


def test_load_from_path():
    car = Car()
    cmd.save(car, 'my_car')

    # Try with string first
    assert cmd.load('my_car') is car

    # Try with path
    assert cmd.load(pyos.PyosPath('my_car')) is car
