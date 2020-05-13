import pytest

import mincepy
from mincepy.testing import Car

import pyos


def test_overwrite(historian: mincepy.Historian):
    car = Car()
    car_id = pyos.db.save_one(car, 'car')
    del car

    with pytest.raises(mincepy.DuplicateKeyError):
        pyos.db.save_one(Car(), 'car')

    # Now use the overwrite settings
    new_car = Car()
    pyos.db.save_one(new_car, 'car', overwrite=True)
    del new_car

    with pytest.raises(mincepy.NotFound):
        historian.load(car_id)
