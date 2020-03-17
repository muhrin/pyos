from mincepy.testing import *

from pyos import pyos, lib


def test_locate():
    car = Car()
    car.save()
    cwd = pyos.pwd()

    assert str(pyos.locate(car)[0]).startswith(str(cwd))
