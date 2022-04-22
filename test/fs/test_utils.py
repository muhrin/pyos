# -*- coding: utf-8 -*-
from mincepy import testing

import pyos.os
from pyos import psh
from pyos import fs


def test_find_multiple_paths():
    """Test the find function when specifying multiple start points"""
    ferrari = testing.Car(make='ferrari')
    skoda = testing.Car(make='skoda')

    pyos.os.makedirs('path1/')
    pyos.os.makedirs('path2/')

    psh.save(ferrari, 'path1/ferrari')
    psh.save(skoda, 'path2/skoda')

    assert len(fs.find(type=testing.Car)) == 2
    assert len(fs.find('path1/')) == 1
    assert len(fs.find('path1/', type=testing.Car)) == 1

    # Multiple paths
    assert len(fs.find('path1/', 'path2/')) == 2
    assert len(fs.find('path1/', 'path2/', type=testing.Car)) == 2


def test_find_from_meta():
    ferrari = testing.Car(make='ferrari')
    skoda = testing.Car(make='skoda')

    pyos.db.save_one(ferrari, meta=dict(num_keys=1))
    pyos.db.save_one(skoda, meta=dict(num_keys=2))

    res = fs.find(meta=dict(num_keys=2))
    assert len(res) == 1
    assert res[0].obj is skoda


def test_find_from_attribute():
    ferrari = testing.Car(make='ferrari')
    skoda = testing.Car(make='skoda')
    pyos.db.save_many((ferrari, skoda))

    res = fs.find(obj_filter=testing.Car.make == 'skoda')
    assert len(res) == 1
    assert res[0].obj is skoda
