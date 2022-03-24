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
