from mincepy.testing import Car

from pyos import pyos


def test_load_single():
    """Test loading a single objects just returns that object and not a list"""
    car = Car()
    car_id = car.save()
    loaded = pyos.load(car_id)
    assert loaded is car


def test_load_from_path():
    car = Car()
    pyos.save(car, 'my_car')

    # Try with string first
    assert pyos.load('my_car') is car

    # Try with path
    assert pyos.load(pyos.PyosPath('my_car')) is car
