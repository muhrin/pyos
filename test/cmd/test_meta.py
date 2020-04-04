from mincepy.testing import Car

from pyos import cmd


def dict_in(where: dict, what: dict):
    for key, value in what.items():
        if key not in where or where[key] != value:
            return False

    return True


def test_meta_basic():
    car = Car()
    car.save()

    cmd.meta(-cmd.s, car, fast=True, colour='blue')
    assert dict_in(cmd.meta(car), {'fast': True, 'colour': 'blue'})

    cmd.meta(-cmd.u, car, fast=False)
    assert dict_in(cmd.meta(car), {'fast': False, 'colour': 'blue'})


def test_meta_update_upsert():
    """Test that update automatically upserts i.e. if there is no metadata for an object and
    update is called it still just sets the metadata"""
    car = Car()
    car.save()

    orig = cmd.meta(car)

    cmd.meta(-cmd.u, car, fast=True, colour='blue')
    assert dict_in(cmd.meta(car), {'fast': True, 'colour': 'blue'})


def test_meta_many():
    car1 = Car().save()
    car2 = Car().save()

    new_meta = {'fast': True, 'colour': 'blue'}

    cmd.meta(-cmd.s, car1, car2, fast=True, colour='blue')
    assert dict_in(cmd.meta(car1), new_meta)
    assert dict_in(cmd.meta(car2), new_meta)
