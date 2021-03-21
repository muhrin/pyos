# -*- coding: utf-8 -*-
from mincepy import testing

from pyos import db
from pyos import os


def test_rename():
    car = testing.Car()
    car_path = '/home/sub/subsub/my_car'
    db.save_one(car, car_path)

    car_path = db.get_path(car)
    assert car_path == '/home/sub/subsub/my_car'
    os.rename(car_path, '/home/new/your_car')
    assert db.get_path(car) == '/home/new/your_car'

    os.rename('/home/new/your_car', 'their_car')
    assert db.get_path(car) == '/home/new/their_car'
