from mincepy.testing import Car

from pyos import pyos


def test_locate():
    car = Car()
    car.save()
    cwd = pyos.pwd()

    assert str(pyos.locate(car)[0].abspath).startswith(str(cwd))
