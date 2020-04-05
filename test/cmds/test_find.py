from mincepy.testing import Car, Person

from pyos import cmds


def fill_with_cars(subdirs: list):
    cwd = cmds.pwd()
    for subdir in subdirs:
        cmds.cd(subdir)
        car = Car()
        car.save(with_meta={'target': True, 'mydir': subdir})
    # Now change back to the original directory
    cmds.cd(cwd)


def test_simple_find():
    # Save a car
    car = Car()
    car.save(with_meta={'group': 'cars'})

    # Look for it
    results = cmds.find(meta=dict(group='cars'))
    assert len(results) == 1
    assert results[0].obj_id == car.obj_id

    # Add another car to the group
    car2 = Car()
    car2.save(with_meta={'group': 'cars'})

    # Look for them
    results = cmds.find(meta=dict(group='cars'))
    assert len(results) == 2
    assert car.obj_id in results
    assert car2.obj_id in results


def test_subdirs_find():
    subdirs = ['./', 'a/', 'b/', 'c/', 'd/']
    fill_with_cars(subdirs)
    num_subdirs = len(subdirs)

    results = cmds.find(meta=dict(target=True))
    assert len(results) == num_subdirs

    # Check mindepth
    for idx, subdir in enumerate(subdirs):
        found = cmds.find(mindepth=idx)
        assert len(found) == num_subdirs - idx
        dirs = {cmds.meta(node)['mydir'] for node in found}
        for check_dir in subdirs[idx:]:
            assert check_dir in dirs

    # Now check maxdepth
    for idx, subdir in enumerate(subdirs):
        # Note, have to use +1 on indexes here because of the 'exclusive' range notations, etc
        found = cmds.find(maxdepth=idx)
        assert len(found) == idx + 1
        dirs = {cmds.meta(node)['mydir'] for node in found}
        for check_dir in subdirs[:idx + 1]:
            assert check_dir in dirs

    # Now check combinations of mindepth and maxdepth

    for min_idx in range(len(subdirs)):
        for max_idx in range(min_idx, len(subdirs)):
            found = cmds.find(mindepth=min_idx, maxdepth=max_idx)
            assert len(found) == max_idx - min_idx + 1
            dirs = {cmds.meta(node)['mydir'] for node in found}

            for check_dir in subdirs[min_idx:max_idx + 1]:
                assert check_dir in dirs


def test_find_starting_point():
    """Test that find respects the passed starting points"""
    subdirs = ['./', 'a/', 'b/', 'c/', 'd/']
    fill_with_cars(subdirs)
    num_subdirs = len(subdirs)

    for idx, subdir in enumerate(subdirs):
        start_point = "/".join(subdirs[:idx + 1])
        found = cmds.find(start_point)
        assert len(found) == num_subdirs - idx
        dirs = {cmds.meta(meta_dict)['mydir'] for meta_dict in found}

        for check_dir in subdirs[idx:]:
            assert check_dir in dirs


def test_find_by_type_simple():
    car = Car()
    car.save()
    person = Person('martin', 34)
    person.save()

    results = cmds.find(type=Car)
    assert len(results) == 1
    assert results[0].obj is car

    results = cmds.find(type=Person)
    assert len(results) == 1
    assert results[0].obj is person
