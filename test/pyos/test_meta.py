from mincepy.testing import Car

from pyos import pyos


def copy_update(target: dict, update: dict):
    new = target.copy()
    new.update(update)
    return new


def dict_in(where: dict, what: dict):
    for key, value in what.items():
        if key not in where or where[key] != value:
            return False

    return True


def test_meta_basic():
    car = Car()
    car.save()

    orig = pyos.meta(car)  # Need to get the origin as pyos uses it to store certain settings

    pyos.meta(-pyos.s, car, fast=True, colour='blue')
    assert pyos.meta(car) == copy_update(orig, {'fast': True, 'colour': 'blue'})

    pyos.meta(-pyos.u, car, fast=False)
    assert pyos.meta(car) == copy_update(orig, {'fast': False, 'colour': 'blue'})


def test_meta_update_upsert():
    """Test that update automatically upserts i.e. if there is no metadata for an object and
    update is called it still just sets the metadata"""
    car = Car()
    car.save()

    orig = pyos.meta(car)

    pyos.meta(-pyos.u, car, fast=True, colour='blue')
    assert pyos.meta(car) == copy_update(orig, {'fast': True, 'colour': 'blue'})


def test_meta_many():
    car1 = Car()
    car2 = Car()

    new_meta = {'fast': True, 'colour': 'blue'}

    pyos.meta(-pyos.s, car1, car2, fast=True, colour='blue')
    assert dict_in(pyos.meta(car1), new_meta)
    assert dict_in(pyos.meta(car2), new_meta)
