# -*- coding: utf-8 -*-
from mincepy.testing import Car, Person

import pyos
from pyos import psh

# Disable this here because, e.g., ls() causes the linter to warn because it is the
# decorator that takes care of passing the first argument
# pylint: disable=no-value-for-parameter


def test_ls_basic():
    assert len(psh.ls()) == 0

    car1 = Car()
    car1.save()

    assert len(psh.ls()) == 1

    # Now save in a different directory
    psh.cd('test')

    assert len(psh.ls()) == 0

    car = Car()
    car.save()

    assert len(psh.ls()) == 1

    psh.cd('..')
    contents = psh.ls()
    assert len(contents) == 2  # Now there is a directory and a file
    found = []
    for entry in contents:
        if isinstance(entry, pyos.fs.DirectoryNode):
            assert entry.name == 'test/'
            found.append(True)
            continue

        if isinstance(entry, pyos.fs.ObjectNode):
            assert entry.obj_id == car1.obj_id
            found.append(True)
            continue
    assert len(found) == 2


def test_ls_path():
    """Test that ls lists the contents of a folder when given a path"""
    car = Car()
    psh.save(car, 'a/')

    res = psh.ls()
    assert len(res) == 1  # Should have the directory in home
    assert 'a/' in repr(res)

    res = psh.ls('a/')
    assert len(res) == 1
    assert str(car.obj_id) in repr(res)


def test_ls_dirs():
    subdirs = ['a/', 'b/', 'c/', 'd/']
    for subdir in subdirs:
        # Put a couple of cars in just to make it more realistic
        psh.save(Car(), subdir)
        psh.save(Car(), subdir)

    results = psh.ls()
    assert len(results) == len(subdirs)
    for result in results:
        assert isinstance(result, pyos.fs.DirectoryNode)
        idx = subdirs.index(result.name)
        assert idx != -1
        subdirs.pop(idx)
    assert not subdirs


def test_ls_minus_d():
    # Two cars at top level and two in the garage
    psh.save(Car())
    psh.save(Car())
    psh.save(Car(), 'garage/')
    psh.save(Car(), 'garage/')

    # The two cars, plus the directory
    assert len(psh.ls()) == 3

    # Just the current directory
    results = psh.ls(-psh.d)
    assert len(results) == 1
    assert results[0].abspath == psh.pwd()


def test_ls_lots():
    paths = ['test/', 'b/', 'test/b/', 'my_dir/', 'my_dir/sub/', 'test/b/b_sub/']
    num = len(paths)
    for idx in range(20):
        psh.save(Car(), paths[idx % num])
        psh.save(Person('random', 35), paths[idx % num])

    # Now save some in the root
    for _ in range(2):
        Car().save()
        Person('person a', 23).save()

    # We should have 3 paths and 4 objects
    results = psh.ls()

    assert len(results) == 7


def test_ls_minus_l():
    car1_id = psh.save(Car())
    car2_id = psh.save(Car())
    car3_id = psh.save(Car(), 'garage/')
    car4_id = psh.save(Car(), 'garage/')

    res = psh.ls(-psh.l)
    assert len(res) == 3
    res_repr = repr(res)
    assert 'garage' in res_repr
    assert str(car1_id) in res_repr
    assert str(car2_id) in res_repr
    assert str(car3_id) not in res_repr
    assert str(car4_id) not in res_repr

    res = psh.ls(-psh.l, 'garage/')
    assert len(res) == 2
    res_repr = repr(res)
    assert 'garage' not in res_repr
    assert str(car1_id) not in res_repr
    assert str(car2_id) not in res_repr
    assert str(car3_id) in res_repr
    assert str(car4_id) in res_repr


def test_inexistent():
    """This used to raise but shouldn't do make sure it's possible"""
    assert len(psh.ls('not_there')) == 0


def test_vanishing_folders():
    """Test for bug we had where folders would vanish if changed to their parent directory"""
    psh.cd('/test/')
    car_id = psh.save(Car())
    results = psh.ls()
    assert len(results) == 1
    assert results[0].obj_id == car_id

    results = psh.ls('/')
    assert len(results) == 1
    assert results[0].abspath == pyos.Path('/test/')
