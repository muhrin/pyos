# -*- coding: utf-8 -*-
from pytray import obj_load

from mincepy.testing import Car, Person

import pyos.os
from pyos import psh


def fill_with_cars(subdirs: list):
    cwd = psh.pwd()
    for subdir in subdirs:
        pyos.os.makedirs(subdir, exists_ok=True)
        psh.cd(subdir)
        car = Car()
        car.save(meta={'target': True, 'mydir': subdir})
    # Now change back to the original directory
    psh.cd(cwd)


def test_simple_find():
    # Save a car
    car = Car()
    car.save(meta={'group': 'cars'})

    # Look for it
    results = psh.find(meta=dict(group='cars'))
    assert len(results) == 1
    assert results[0].entry_id == car.obj_id

    # Add another car to the group
    car2 = Car()
    car2.save(meta={'group': 'cars'})

    # Look for them
    results = psh.find(meta=dict(group='cars'))
    assert len(results) == 2
    assert car.obj_id in results
    assert car2.obj_id in results


def test_find_paths():
    pyos.os.makedirs('subdir/')
    psh.save(Car(), 'subdir/car_a')

    res = psh.find()
    assert len(res) == 1
    assert res[0].abspath == pyos.pathlib.Path('subdir/car_a').resolve()
    assert 'subdir/car_a' in str(res)


def test_subdirs_find():
    subdirs = ['./', 'a/', 'b/', 'c/', 'd/']
    fill_with_cars(subdirs)
    num_subdirs = len(subdirs)

    results = psh.find(meta=dict(target=True))
    assert len(results) == num_subdirs

    # Check mindepth
    for idx, _subdir in enumerate(subdirs):
        found = psh.find(mindepth=idx + 1)
        assert len(found) == num_subdirs - idx
        dirs = {psh.meta(node)['mydir'] for node in found}
        for check_dir in subdirs[idx:]:
            assert check_dir in dirs

    # Now check maxdepth
    for idx, _subdir in enumerate(subdirs):
        found = psh.find(maxdepth=idx)
        assert len(found) == idx
        dirs = {psh.meta(node)['mydir'] for node in found}
        for check_dir in subdirs[:idx]:
            assert check_dir in dirs

    # Now check combinations of mindepth and maxdepth
    for min_idx in range(len(subdirs)):
        for max_idx in range(min_idx, len(subdirs)):
            found = psh.find(mindepth=min_idx, maxdepth=max_idx)
            assert len(found) == max_idx - min_idx if min_idx == 0 else (max_idx - min_idx + 1)
            dirs = {psh.meta(node)['mydir'] for node in found}

            for check_dir in subdirs[min_idx:max_idx]:
                assert check_dir in dirs


def test_find_starting_point():
    """Test that find respects the passed starting points"""
    subdirs = ['./', 'a/', 'b/', 'c/', 'd/']
    fill_with_cars(subdirs)
    num_subdirs = len(subdirs)

    for idx, _subdir in enumerate(subdirs):
        start_point = '/'.join(subdirs[:idx + 1])
        found = psh.find(start_point)
        assert len(found) == num_subdirs - idx
        dirs = {psh.meta(meta_dict)['mydir'] for meta_dict in found}

        for check_dir in subdirs[idx:]:
            assert check_dir in dirs


def test_find_by_type_simple():
    car = Car()
    car.save()
    person = Person('martin', 34)
    person.save()

    results = psh.find(type=Car)
    assert len(results) == 1
    assert results[0].obj is car

    results = psh.find(type=Person)
    assert len(results) == 1
    assert results[0].obj is person


def test_shell_find(pyos_shell):
    # Save a car
    car = Car()
    car.save(meta={'group': 'cars'})

    # Look for it
    res = pyos_shell.app_cmd(f'find -t {obj_load.full_name(Car)} -m group=cars')
    assert not res.stderr
    assert str(car.obj_id) in res.stdout

    # Add another car to the group
    car2 = Car()
    car2.save(meta={'group': 'cars'})

    # Look for them
    res = pyos_shell.app_cmd(f'find -t {obj_load.full_name(Car)} -m group=cars')
    assert not res.stderr
    assert str(car.obj_id) in res.stdout
    assert str(car2.obj_id) in res.stdout


def test_shell_find_starting_point(pyos_shell):
    """Test that find respects the passed starting points"""
    subdirs = ['./', 'a/', 'b/', 'c/', 'd/']
    fill_with_cars(subdirs)
    num_subdirs = len(subdirs)

    for idx, _subdir in enumerate(subdirs):
        start_point = '/'.join(subdirs[:idx + 1])
        res = pyos_shell.app_cmd(f'find -s {start_point}')
        assert not res.stderr

        paths = tuple(map(str.strip, res.stdout.split('\n')[:-1]))
        assert len(paths) == num_subdirs - idx
        dirs = {psh.meta(path)['mydir'] for path in paths}

        for check_dir in subdirs[idx:]:
            assert check_dir in dirs


def test_shell_find_by_type_simple(pyos_shell):
    car = Car()
    car.save()
    person = Person('martin', 34)
    person.save()

    res = pyos_shell.app_cmd(f'find -t {obj_load.full_name(Car)}')
    assert not res.stderr
    lines = res.stdout.split('\n')[:-1]
    assert len(lines) == 1
    assert str(car.obj_id) in lines[0]

    res = pyos_shell.app_cmd(f'find -t {obj_load.full_name(Person)}')
    assert not res.stderr
    lines = res.stdout.split('\n')[:-1]
    assert len(lines) == 1
    assert str(person.obj_id) in lines[0]


def test_shell_find_query_state(pyos_shell):
    fiat = Car(make='fiat', colour='white')
    subaru = Car(make='subaru', colour='white')
    fiat.save()
    subaru.save()

    # =
    res = pyos_shell.app_cmd(f'find -t {obj_load.full_name(Car)} colour=white')
    assert not res.stderr
    lines = res.stdout.split('\n')[:-1]
    assert len(lines) == 2
    assert str(fiat.obj_id) in res.stdout
    assert str(subaru.obj_id) in res.stdout

    res = pyos_shell.app_cmd('find make=subaru')
    assert not res.stderr
    lines = res.stdout.split('\n')[:-1]
    assert len(lines) == 1
    assert str(subaru.obj_id) in lines[0]

    # !=
    res = pyos_shell.app_cmd(f'find -t {obj_load.full_name(Car)} make!=fiat')
    assert not res.stderr
    lines = res.stdout.split('\n')[:-1]
    assert len(lines) == 1
    assert str(fiat.obj_id) not in res.stdout
    assert str(subaru.obj_id) in res.stdout
