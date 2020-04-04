from mincepy.testing import Car, Person

import pyos
from pyos import cmd


def test_ls_basic():
    assert len(cmd.ls()) == 0

    car1 = Car()
    car1.save()

    assert len(cmd.ls()) == 1

    # Now save in a different directory
    cmd.cd('test')

    assert len(cmd.ls()) == 0

    car = Car()
    car.save()

    assert len(cmd.ls()) == 1

    cmd.cd('..')
    contents = cmd.ls()
    assert len(contents) == 2  # Now there is a directory and a file
    found = []
    for entry in contents:
        if isinstance(entry, pyos.DirectoryNode):
            assert entry.name == 'test/'
            found.append(True)
            continue

        if isinstance(entry, pyos.ObjectNode):
            assert entry.obj_id == car1.obj_id
            found.append(True)
            continue
    assert len(found) == 2


def test_ls_path():
    """Test that ls lists the contents of a folder when given a path"""
    car = Car()
    cmd.save(car, 'a/')

    assert len(cmd.ls()) == 1  # Should have the directory in home
    assert len(cmd.ls('a/')) == 1


def test_ls_dirs():
    subdirs = ['a/', 'b/', 'c/', 'd/']
    for subdir in subdirs:
        # Put a couple of cars in just to make it more realistic
        cmd.save(Car(), subdir)
        cmd.save(Car(), subdir)

    results = cmd.ls()
    assert len(results) == len(subdirs)
    for result in results:
        assert isinstance(result, pyos.DirectoryNode)
        idx = subdirs.index(result.name)
        assert idx != -1
        subdirs.pop(idx)
    assert not subdirs


def test_ls_minus_d():
    # Two cars at top level and two in the garage
    cmd.save(Car())
    cmd.save(Car())
    cmd.save(Car(), 'garage/')
    cmd.save(Car(), 'garage/')

    # The two cars, plus the directory
    assert len(cmd.ls()) == 3

    # Just the current directory
    results = cmd.ls(-pyos.cmd.d)
    assert len(results) == 1
    assert results[0].abspath == cmd.pwd()


def test_ls_lots():
    paths = ['test/', 'b/', 'test/b/', 'my_dir/', 'my_dir/sub/', 'test/b/b_sub/']
    num = len(paths)
    for idx in range(20):
        cmd.save(Car(), paths[idx % num])
        cmd.save(Person('random', 35), paths[idx % num])

    # Now save some in the root
    for _ in range(2):
        Car().save()
        Person('person a', 23).save()

    # We should have 3 paths and 4 objects
    results = cmd.ls()

    assert len(results) == 7


def test_ls_minus_l():
    cmd.save(Car())
    cmd.save(Car())
    cmd.save(Car(), 'garage/')
    cmd.save(Car(), 'garage/')

    assert len(cmd.ls(-cmd.l)) == 3
    assert len(cmd.ls(-cmd.l, 'garage/')) == 2


def test_inexistent():
    """This used to raise but shouldn't do make sure it's possible"""
    assert len(cmd.ls('not_there')) == 0
