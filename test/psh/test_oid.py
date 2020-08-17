from mincepy.testing import Car

from pyos.psh import cmds


def test_oid_simple():
    car = Car()
    car.save()

    assert cmds.oid(car) == car.obj_id

    # Save some more and see if the order is preserved
    cars = []
    for _ in range(10):
        cars.append(Car())

    cmds.save(*cars)  # pylint: disable=no-value-for-parameter
    results = cmds.oid(*cars)
    for car, result_oid in zip(cars, results):
        assert car.obj_id == result_oid
    assert len(cars) == len(results)
