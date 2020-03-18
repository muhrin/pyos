from mincepy.testing import Car

from pyos import pyos


def fill_with_cars(subdirs: list):
    cwd = pyos.pwd()
    for subdir in subdirs:
        pyos.cd(subdir)
        car = Car()
        car.save(with_meta={'target': True, 'mydir': subdir})
    # Now change back to the original directory
    pyos.cd(cwd)


def test_simple_find():
    # Save a car
    car = Car()
    car.save(with_meta={'group': 'cars'})

    # Look for it
    results = pyos.find(group='cars')
    assert len(results) == 1
    assert results[0].obj_id == car.obj_id

    # Add another car to the group
    car2 = Car()
    car2.save(with_meta={'group': 'cars'})

    # Look for them
    results = pyos.find(group='cars')
    assert len(results) == 2
    assert car.obj_id in results
    assert car2.obj_id in results


def test_subdirs_find():
    subdirs = ['./', 'a/', 'b/', 'c/', 'd/']
    fill_with_cars(subdirs)
    num_subdirs = len(subdirs)

    results = pyos.find(target=True)
    assert len(results) == num_subdirs

    # Check mindepth
    for idx, subdir in enumerate(subdirs):
        found = pyos.find(pyos.mindepth(idx))
        assert len(found) == num_subdirs - idx
        dirs = {pyos.meta(node)['mydir'] for node in found}
        for check_dir in subdirs[idx:]:
            assert check_dir in dirs

    # Now check maxdepth
    for idx, subdir in enumerate(subdirs):
        # Note, have to use +1 on indexes here because of the 'exclusive' range notations, etc
        found = pyos.find(pyos.maxdepth(idx))
        assert len(found) == idx + 1
        dirs = {pyos.meta(node)['mydir'] for node in found}
        for check_dir in subdirs[:idx + 1]:
            assert check_dir in dirs

    # Now check combinations of mindepth and maxdepth

    for min_idx in range(len(subdirs)):
        for max_idx in range(min_idx, len(subdirs)):
            found = pyos.find(pyos.mindepth(min_idx), pyos.maxdepth(max_idx))
            assert len(found) == max_idx - min_idx + 1
            dirs = {pyos.meta(node)['mydir'] for node in found}

            for check_dir in subdirs[min_idx:max_idx + 1]:
                assert check_dir in dirs


def test_find_starting_point():
    """Test that find respects the passed starting points"""
    subdirs = ['./', 'a/', 'b/', 'c/', 'd/']
    fill_with_cars(subdirs)
    num_subdirs = len(subdirs)

    for idx, subdir in enumerate(subdirs):
        start_point = "/".join(subdirs[:idx + 1])
        found = pyos.find(start_point)
        assert len(found) == num_subdirs - idx
        dirs = {pyos.meta(meta_dict)['mydir'] for meta_dict in found}

        for check_dir in subdirs[idx:]:
            assert check_dir in dirs
