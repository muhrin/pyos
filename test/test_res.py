import getpass

from mincepy.testing import *

from pyos import res, fmt


def test_obj_id_list_simple(historian):
    car = Car()
    car.save()
    record = historian.get_current_record(car)

    obj_ids = res.ObjIdList()
    obj_ids.append(car.obj_id)

    represent = obj_ids.__repr__()
    assert represent.strip() == str(car.obj_id)

    obj_ids.show_types = True
    represent = obj_ids.__repr__()

    assert str(car.obj_id) in represent
    assert fmt.pretty_type_string(Car) in represent

    obj_ids.show_mtime = True
    represent = obj_ids.__repr__()

    assert str(car.obj_id) in represent
    assert fmt.pretty_type_string(Car) in represent
    assert fmt.pretty_datetime(record.snapshot_time) in represent

    obj_ids.show_user = True
    represent = obj_ids.__repr__()

    assert str(car.obj_id) in represent
    assert fmt.pretty_type_string(Car) in represent
    assert fmt.pretty_datetime(record.snapshot_time) in represent
    assert getpass.getuser() in represent

    obj_ids.show_version = True
    represent = obj_ids.__repr__()

    assert str(car.obj_id) in represent
    assert fmt.pretty_type_string(Car) in represent
    assert fmt.pretty_datetime(record.snapshot_time) in represent
    assert getpass.getuser() in represent
    assert " 0 " in represent

    obj_ids.show_loaded = True
    represent = obj_ids.__repr__()

    assert str(car.obj_id) in represent
    assert fmt.pretty_type_string(Car) in represent
    assert fmt.pretty_datetime(record.snapshot_time) in represent
    assert getpass.getuser() in represent
    assert " 0 " in represent
    assert "*" in represent

    del car

    obj_ids.refresh()
    represent = obj_ids.__repr__()
    assert "*" not in represent
