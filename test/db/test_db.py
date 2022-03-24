# -*- coding: utf-8 -*-

import pytest

import mincepy
from mincepy.testing import Car

import pyos.exceptions
from pyos import db


def test_overwrite(historian: mincepy.Historian):
    car = Car()
    car_id = db.save_one(car, 'car')
    del car

    with pytest.raises(pyos.exceptions.FileExistsError):
        db.save_one(Car(), 'car')

    # Now use the overwrite settings
    new_car = Car()
    db.save_one(new_car, 'car', overwrite=True)
    del new_car

    with pytest.raises(mincepy.NotFound):
        historian.load(car_id)


def test_getting_obj_id():
    car = Car()
    car_id = db.save_one(car, 'my_car')

    assert next(db.get_oid(car_id)) == car_id
    assert next(db.get_oid(car)) == car_id
    assert next(db.get_oid(str(car_id))) == car_id
    assert next(db.get_oid('my_car')) == car_id
    assert next(db.get_oid(f'./{car_id}')) == car_id


def test_save_meta():
    car = Car()
    car_id = db.save_one(car, 'my_car', meta=dict(license='abcdef'))
    assert db.get_meta(car_id)['license'] == 'abcdef'
