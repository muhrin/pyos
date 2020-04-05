from mincepy.testing import Car

from pyos.pysh import cmds


def test_oid_simple():
    car = Car()
    car.save()

    assert cmds.oid(car) == car.obj_id

    # Save some more and see if the order is preserved
    cars = []
    for _ in range(10):
        cars.append(Car())

    cmds.save(*cars)
    assert cmds.oid(*cars) == [car.obj_id for car in cars]
