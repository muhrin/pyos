from mincepy.testing import Car

import pyos
from pyos import psh
import pyos.os


def test_simple():
    car = Car()
    car.save()
    home = pyos.Path().resolve()
    assert psh.locate(car) == home / str(car.obj_id)


def test_locate_multiple():
    car1 = Car()
    car2 = Car()

    pyos.os.makedirs("garage1/")
    pyos.os.makedirs("garage2/")

    car1.save()
    car2.save()
    car1_path = (pyos.Path("garage1/") / str(car1.obj_id)).resolve()
    car2_path = (pyos.Path("garage2/") / str(car2.obj_id)).resolve()
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


def test_locate_nodes_and_paths():
    """locate should also take paths and filesystem nodes, e.g. the results of find"""
    pyos.os.makedirs("garage/")
    car = Car(make="ferrari")
    psh.save(car, "garage/ferrari")
    expected = pyos.Path("garage/ferrari").resolve()

    assert psh.locate("garage/ferrari") == expected
    assert psh.locate(psh.find(state=dict(make="ferrari"))) == expected
    assert (psh.find(state=dict(make="ferrari")) | psh.locate) == expected
