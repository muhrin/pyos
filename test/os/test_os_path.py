# -*- coding: utf-8 -*-
import re

from mincepy.testing import Car

import pyos
from pyos import os


def test_normpath_curdir():
    """Using normpath(curdir), i.e. '.' should normalise to './'"""
    assert pyos.os.path.normpath('.') == './'


def test_exists():
    """Check some properties of the exists function"""
    car = Car()
    car_path = '/home/sub/subsub/my_car'
    pyos.db.save_one(car, car_path)

    # Make sure the car and all subdirectories exist
    # parts = pyos.os.path.split(car_path)
    parts = re.findall(r'(\w*/|\w+$)', car_path)
    for idx in range(1, len(parts)):
        assert pyos.os.path.exists(''.join(parts[:idx]))


def test_normpath_parent_dir():
    assert os.path.normpath('a/b/../') == 'a/'
    assert os.path.normpath('a/b/..') == 'a/'


def test_normpah_current_dir():
    assert os.path.normpath('a/b/./') == 'a/b/'
    assert os.path.normpath('a/b/.') == 'a/b/'
