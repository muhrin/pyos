from mincepy.testing import Car

import pyos
from pyos import psh


def test_simple():
    car = Car()
    car.save()
    home = pyos.Path().resolve()
    assert psh.locate(car) == home / str(car.obj_id)


def test_locate_multiple():
    car1 = Car()
    car2 = Car()
    car1_path = (pyos.Path('garage1/') / str(car1.obj_id)).resolve()
    car2_path = (pyos.Path('garage2/') / str(car2.obj_id)).resolve()
    pyos.db.save_many([(car1, car1_path), (car2, car2_path)])

    # By object
    locations = psh.locate(car1, car2)
    assert locations[0] == car1_path
    assert locations[1] == car2_path

    # By obj id
    locations = psh.locate(car1.obj_id, car2)
    assert locations[0] == car1_path
    assert locations[1] == car2_path

    # By obj id string
    locations = psh.locate(str(car1.obj_id), car2.obj_id)
    assert locations[0] == car1_path
    assert locations[1] == car2_path
