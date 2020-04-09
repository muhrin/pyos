import pytest

import mincepy
from mincepy.testing import Car

from pyos import psh


def test_rm_basic():
    """Delete by the various identifier"""
    car = Car()
    psh.save(car)

    assert len(psh.ls()) == 1
    psh.rm(car)
    assert len(psh.ls()) == 0

    car_id = Car().save()
    assert len(psh.ls()) == 1
    psh.rm(car_id)
    assert len(psh.ls()) == 0

    car_id = Car().save()
    assert len(psh.ls()) == 1
    psh.rm(str(car_id))
    assert len(psh.ls()) == 0


def test_rm_multiple(historian: mincepy.Historian):
    car1 = Car()
    car2 = Car()
    car3 = Car()

    psh.save(car1, car2, car3)
    assert len(psh.ls()) == 3
    psh.rm(car1, car2)
    assert len(psh.ls()) == 1

    assert not car1.is_saved()
    assert not car2.is_saved()
    assert car3.is_saved()


def test_rm_directory():
    car1 = Car()
    psh.save(car1)
    psh.cd('/cars/')
    car2 = Car()
    car3 = Car()
    psh.save(car2, car3)

    assert len(psh.ls('/cars/')) == 2

    # First without -r flag
    psh.rm('/cars/')
    assert len(psh.ls('/cars/')) == 2
    assert car1.is_saved()
    assert car2.is_saved()
    assert car3.is_saved()

    # Now with
    psh.rm(-psh.r, '/cars/')
    assert len(psh.ls('/cars/')) == 0
    assert car1.is_saved()
    assert not car2.is_saved()
    assert not car3.is_saved()
