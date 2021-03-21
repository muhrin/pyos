# -*- coding: utf-8 -*-
from mincepy.testing import Car

import pyos
from pyos import psh


def test_load_single():
    """Test loading a single objects just returns that object and not a list"""
    car = Car()
    car_id = car.save()
    loaded = psh.load(car_id)
    assert loaded is car


def test_load_from_path():
    car = Car()
    psh.save(car, 'my_car')

    # Try with string first
    assert psh.load('my_car') is car

    # Try with path
    assert psh.load(pyos.pathlib.Path('my_car')) is car


def test_load_from_obj_id_string():
    car = Car()
    car_id = psh.save(car)

    loaded = psh.load(str(car_id))
    assert loaded is car
