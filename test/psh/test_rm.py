# -*- coding: utf-8 -*-
import mincepy
from mincepy.testing import Car

import pyos.os
from pyos import psh

# pylint: disable=no-value-for-parameter


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


def test_rm_multiple(historian: mincepy.Historian):  # pylint: disable=unused-argument
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
    pyos.os.makedirs('/cars/')

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


def test_rm_objects_with_references():
    """Test deleting objects in a directory that reference each other"""
    pyos.os.makedirs('/cars/garage/')

    num_cars = 10
    psh.cd('/cars/garage/')
    for _ in range(num_cars):
        Car().save()

    psh.cd('/cars/')
    cars = mincepy.RefList()
    cars.extend(psh.load(psh.ls('garage/')))

    psh.save(cars)
    results = psh.ls()
    assert len(results) == 2  # the list plus the 'garage' folder

    psh.cd('/')
    # Delete the folder
    psh.rm - psh.r('/cars/')  # pylint: disable=expression-not-assigned

    assert len(psh.ls('/cars/')) == 0
