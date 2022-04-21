# -*- coding: utf-8 -*-
import mincepy

from pyos import os as pos
from pyos import db


def test_delete_outside_pyos(archive_uri):
    car = mincepy.testing.Car()
    car_id = db.save_one(car, 'my_car')
    assert pos.withdb.exists('my_car')

    hist = mincepy.connect(archive_uri, use_globally=False)
    hist.delete(car_id)

    assert not pos.withdb.exists('my_car')
