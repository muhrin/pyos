# -*- coding: utf-8 -*-
import pytest
from mincepy import testing

import pyos.exceptions
from pyos import db
from pyos import os


def test_rename():
    os.makedirs('/home/sub/subsub/')
    os.makedirs('/home/new/')

    car = testing.Car()
    car_path = '/home/sub/subsub/my_car'
    db.save_one(car, car_path)

    car_path = db.get_path(car)
    assert car_path == '/home/sub/subsub/my_car'
    os.rename(car_path, '/home/new/your_car')
    assert db.get_path(car) == '/home/new/your_car'

    os.rename('/home/new/your_car', 'their_car')
    assert db.get_path(car) == os.path.abspath('their_car')


def test_rename_to_existing():
    car1 = testing.Car()
    car2 = testing.Car()
    db.save_many([(car1, 'car1'), (car2, 'car2')])
    assert set(os.listdir()) == {'car1', 'car2'}

    with pytest.raises(pyos.exceptions.FileExistsError):
        os.rename('car2', 'car1')
    assert set(os.listdir()) == {'car1', 'car2'}
