from mincepy.testing import Car

from pyos import cmd


def test_locate():
    car = Car()
    car.save()
    cwd = cmd.pwd()

    assert str(cmd.locate(car)[0].abspath).startswith(str(cwd))
