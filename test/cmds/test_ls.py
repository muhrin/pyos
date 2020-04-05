from mincepy.testing import Car, Person

import pyos
from pyos import cmds


def test_ls_basic():
    assert len(cmds.ls()) == 0

    car1 = Car()
    car1.save()

    assert len(cmds.ls()) == 1

    # Now save in a different directory
    cmds.cd('test')

    assert len(cmds.ls()) == 0

    car = Car()
    car.save()

    assert len(cmds.ls()) == 1

    cmds.cd('..')
    contents = cmds.ls()
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
    cmds.save(car, 'a/')

    assert len(cmds.ls()) == 1  # Should have the directory in home
    assert len(cmds.ls('a/')) == 1


def test_ls_dirs():
    subdirs = ['a/', 'b/', 'c/', 'd/']
    for subdir in subdirs:
        # Put a couple of cars in just to make it more realistic
        cmds.save(Car(), subdir)
        cmds.save(Car(), subdir)

    results = cmds.ls()
    assert len(results) == len(subdirs)
    for result in results:
        assert isinstance(result, pyos.DirectoryNode)
        idx = subdirs.index(result.name)
        assert idx != -1
        subdirs.pop(idx)
    assert not subdirs


def test_ls_minus_d():
    # Two cars at top level and two in the garage
    cmds.save(Car())
    cmds.save(Car())
    cmds.save(Car(), 'garage/')
    cmds.save(Car(), 'garage/')

    # The two cars, plus the directory
    assert len(cmds.ls()) == 3

    # Just the current directory
    results = cmds.ls(-pyos.cmds.d)
    assert len(results) == 1
    assert results[0].abspath == cmds.pwd()


def test_ls_lots():
    paths = ['test/', 'b/', 'test/b/', 'my_dir/', 'my_dir/sub/', 'test/b/b_sub/']
    num = len(paths)
    for idx in range(20):
        cmds.save(Car(), paths[idx % num])
        cmds.save(Person('random', 35), paths[idx % num])

    # Now save some in the root
    for _ in range(2):
        Car().save()
        Person('person a', 23).save()

    # We should have 3 paths and 4 objects
    results = cmds.ls()

    assert len(results) == 7


def test_ls_minus_l():
    cmds.save(Car())
    cmds.save(Car())
    cmds.save(Car(), 'garage/')
    cmds.save(Car(), 'garage/')

    assert len(cmds.ls(-cmds.l)) == 3
    assert len(cmds.ls(-cmds.l, 'garage/')) == 2


def test_inexistent():
    """This used to raise but shouldn't do make sure it's possible"""
    assert len(cmds.ls('not_there')) == 0
