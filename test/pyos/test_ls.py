import pytest

from mincepy.testing import Car, Person

from pyos import pyos, nodes


def test_ls_basic():
    assert len(pyos.ls()) == 0

    car1 = Car()
    car1.save()

    assert len(pyos.ls()) == 1

    # Now save in a different directory
    pyos.cd('test')

    assert len(pyos.ls()) == 0

    car = Car()
    car.save()

    assert len(pyos.ls()) == 1

    pyos.cd('..')
    contents = pyos.ls()
    assert len(contents) == 2  # Now there is a directory and a file
    found = []
    for entry in contents:
        if isinstance(entry, nodes.DirectoryNode):
            assert entry.name == 'test/'
            found.append(True)
            continue

        if isinstance(entry, nodes.ObjectNode):
            assert entry.obj_id == car1.obj_id
            found.append(True)
            continue
    assert len(found) == 2


def test_ls_path():
    """Test that ls lists the contents of a folder when given a path"""
    car = Car()
    pyos.save(car, 'a/')

    assert len(pyos.ls()) == 1  # Should have the directory in home
    assert len(pyos.ls('a/')) == 1


def test_ls_dirs():
    subdirs = ['a/', 'b/', 'c/', 'd/']
    for subdir in subdirs:
        # Put a couple of cars in just to make it more realistic
        pyos.save(Car(), subdir)
        pyos.save(Car(), subdir)

    results = pyos.ls()
    assert len(results) == len(subdirs)
    for result in results:
        assert isinstance(result, nodes.DirectoryNode)
        idx = subdirs.index(result.name)
        assert idx != -1
        subdirs.pop(idx)
    assert not subdirs


def test_ls_minus_d():
    # Two cars at top level and two in the garage
    pyos.save(Car())
    pyos.save(Car())
    pyos.save(Car(), 'garage/')
    pyos.save(Car(), 'garage/')

    # The two cars, plus the directory
    assert len(pyos.ls()) == 3

    # Just the current directory
    results = pyos.ls(-pyos.d)
    assert len(results) == 1
    assert results[0].abspath == pyos.pwd()


def test_ls_inexistent():
    with pytest.raises(ValueError):
        assert not pyos.ls('inexistent')


def test_ls_lots():
    paths = ['test/', 'b/', 'test/b/', 'my_dir/', 'my_dir/sub/', 'test/b/b_sub/']
    num = len(paths)
    for idx in range(20):
        pyos.save(Car(), paths[idx % num])
        pyos.save(Person('random', 35), paths[idx % num])

    # Now save some in the root
    for _ in range(2):
        Car().save()
        Person('person a', 23).save()

    # We should have 3 paths and 4 objects
    results = pyos.ls()
    print(results)

    assert len(results) == 7
