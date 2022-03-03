# -*- coding: utf-8 -*-
from mincepy.testing import Car

from pyos import db
from pyos.psh import cmds


def test_oid():
    car = Car()
    car.save()

    assert cmds.oid(car) == car.obj_id

    # Save some more and see if the order is preserved
    cars = []
    paths = []
    for idx in range(10):
        cars.append(Car())
        paths.append(f'car_{idx}')

    db.save_many(zip(cars, paths))

    results = cmds.oid(*cars)
    for car, result_oid in zip(cars, results):
        assert car.obj_id == result_oid

    assert len(cars) == len(results)

    # Now check paths
    results = cmds.oid(*paths)
    for car, result_oid in zip(cars, results):
        assert car.obj_id == result_oid

    assert len(cars) == len(results)
