# -*- coding: utf-8 -*-
from mincepy.testing import Car

from pyos import psh


def dict_in(where: dict, what: dict):
    for key, value in what.items():
        if key not in where or where[key] != value:
            return False

    return True


def test_meta_basic():
    car = Car()
    car.save()

    psh.meta(-psh.s, car, fast=True, colour='blue')
    assert dict_in(psh.meta(car), {'fast': True, 'colour': 'blue'})

    psh.meta(-psh.u, car, fast=False)
    assert dict_in(psh.meta(car), {'fast': False, 'colour': 'blue'})


def test_meta_update_upsert():
    """Test that update automatically upserts i.e. if there is no metadata for an object and
    update is called it still just sets the metadata"""
    car = Car()
    car.save()
    # Get original
    orig = psh.meta(car)
    # Update and get
    psh.meta(-psh.u, car, fast=True, colour='blue')
    new = psh.meta(car)

    assert dict_in(new, {'fast': True, 'colour': 'blue'})
    assert new != orig


def test_meta_many():
    car1 = Car().save()
    car2 = Car().save()

    new_meta = {'fast': True, 'colour': 'blue'}

    psh.meta(-psh.s, car1, car2, fast=True, colour='blue')
    assert dict_in(psh.meta(car1), new_meta)
    assert dict_in(psh.meta(car2), new_meta)


def test_shell_meta(pyos_shell):
    car = Car()
    car.save(meta={'reg': 123})

    res = pyos_shell.app_cmd('meta {}'.format(car.obj_id))
    assert not res.stderr
    assert 'reg       │123 ' in res.stdout
