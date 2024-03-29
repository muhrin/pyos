# -*- coding: utf-8 -*-
from mincepy.testing import Car

import pyos.os
from pyos import psh

# pylint: disable=no-value-for-parameter


def test_tree_basic():
    Car().save()
    results = psh.tree()
    assert len(results) == 1


def test_tree_depth():
    pyos.os.makedirs('sub/sub/')

    Car().save()
    psh.save(Car(), 'sub/')
    psh.save(Car(), 'sub/sub/')
    psh.save(Car(), 'sub/sub/sub')

    def check_depth(results):
        return results.height

    results = psh.tree()
    assert check_depth(results) == 4
    for idx in range(4):
        height = check_depth(psh.tree - psh.L(idx)())
        assert height == idx + 1


def test_tree_print():
    expected_result = """
├── a
│   ├── b
│   │   └── b_car
│   └── a_car
└── some_car
"""

    pyos.os.makedirs('a/b/')
    psh.save(Car(), 'some_car')
    psh.save(Car(), 'a/a_car')
    psh.save(Car(), 'a/b/b_car')

    results = psh.tree()

    res_string = str(results)

    print(res_string)
    for line in expected_result.split('\n'):
        if line:
            assert line in res_string
