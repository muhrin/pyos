from mincepy.testing import Car

from pyos import pyos


def test_oid_simple():
    car = Car()
    car.save()

    assert pyos.oid(car) == car.obj_id

    # Save some more and see if the order is preserved
    cars = []
    for _ in range(10):
        cars.append(Car())

    pyos.save(*cars)
    assert pyos.oid(*cars) == [car.obj_id for car in cars]
