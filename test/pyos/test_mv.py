from mincepy.testing import Car

from pyos import pyos


def test_mv_basic():
    car = Car()
    car.save()

    # Move to test subdirectory
    pyos.mv(car, 'test/')

    assert pyos.locate(car)[0].abspath == pyos.pwd() / 'test/' / str(car.obj_id)

    contents = pyos.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id

    # Now move test into a subfolder
    pyos.mv('test/', 'sub/')
    contents = pyos.ls()
    assert len(contents) == 1
    assert contents[0].name == 'sub/'

    contents = pyos.ls('sub/')
    assert len(contents) == 1
    assert contents[0].name == 'test/'


def test_mv_from_str():
    car = Car()
    car.save()

    pyos.mv(str(car.obj_id), 'test/')
    contents = pyos.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_from_path():
    car = Car()
    car.save()

    pyos.mv(pyos.locate(car), 'test/')
    contents = pyos.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_from_obj_id():
    car = Car()
    car.save()

    pyos.mv(car.obj_id, 'test/')
    contents = pyos.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_dest_as_path():
    car = Car()
    car.save()

    pyos.mv(car.obj_id, pyos.PyosPath('test/'))
    contents = pyos.ls('test/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_remote():
    """Test moving an object from one remote path to another"""
    car = Car()
    pyos.save(car, '/test/path_a/')
    pyos.mv(car, '/a/different/path/')

    contents = pyos.ls('/a/different/path/')
    assert len(contents) == 1
    assert contents[0].obj_id == car.obj_id


def test_mv_overwrite():
    """Test the moving handles overwriting an existing name correctly"""
    car1 = Car()
    pyos.save(car1, 'my_car')

    car2 = Car()
    car2.save()
    pyos.mv(car2, 'my_car')


def test_mv_no_clobber():
    """Test moving with no clobber"""
    car1 = Car()
    pyos.save(car1, 'my_car')

    car2 = Car()
    pyos.save(car2, 'my_car2')

    assert len(pyos.ls()) == 2
    pyos.mv(-pyos.n, car2, 'my_car')
    assert len(pyos.ls()) == 2  # Still 2
