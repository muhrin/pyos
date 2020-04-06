from mincepy.testing import Car

from pyos.psh import cmds


def test_locate():
    car = Car()
    car.save()
    cwd = cmds.pwd()

    assert str(cmds.locate(car)[0].abspath).startswith(str(cwd))
