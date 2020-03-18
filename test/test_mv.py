from mincepy.testing import Car

from pyos import pyos


def test_mv_basic():
    car = Car()
    car.save()

    # Move to test subdirectory
    pyos.mv(car, 'test/')

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
