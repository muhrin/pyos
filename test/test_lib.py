from mincepy.testing import *

from pyos import lib


def test_get_records_default():
    """Check that objects with no DIR_KEY are still found in the root directory"""
    car = Car()
    car.save()
    # Remove the directory key from the Car
    meta = lib.get_meta(car)[0]
    meta.pop(lib.DIR_KEY)
    lib.set_meta(car, meta=meta)
    assert lib.DIR_KEY not in lib.get_meta(car)

    # Now make sure that it's listed as being present in the root directory
    records = tuple(lib.get_records('/'))
    assert len(records) == 1
    assert records[0]['obj_id'] == car.obj_id
