from mincepy.testing import Car
import pytest

from pyos import psh


def test_history():
    car = Car("ferrari", "red")
    psh.save(car, "my_car")
    car.colour = "blue"
    car.save()

    versions = psh.history(car, representer=str)
    assert list(versions) == ["red ferrari", "blue ferrari"]
    # The object can also be given by path or id
    assert list(psh.history("my_car", representer=str)) == ["red ferrari", "blue ferrari"]
    assert list(psh.history(car.obj_id, representer=str)) == ["red ferrari", "blue ferrari"]


def test_history_of_a_directory():
    psh.mkdir("garage/")
    psh.save(Car(), "garage/car")
    with pytest.raises(ValueError, match="not an object"):
        psh.history("garage/")
