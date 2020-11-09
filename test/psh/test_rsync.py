# -*- coding: utf-8 -*-
import mincepy.testing as mince_testing
import yarl

from pyos import psh
from pyos import os


def get_uri_with_objsys_path(archive_uri: str, path: str):
    if path.startswith(os.sep):
        path = path[1:]
    return str(yarl.URL(archive_uri) / path)


def test_rsync_basic(historian, test_utils):
    car = mince_testing.Car()
    person = mince_testing.Person('martin', 35, car=car)
    historian.save(car, person)

    with test_utils.temporary_historian('test-rsync') as (uri, _remote):
        dest = get_uri_with_objsys_path(uri, 'home/')
        result = psh.rsync('./', dest)
        assert car.obj_id in result
        assert person.obj_id in result

        # Make a mutation and see if it is synced
        person.age = 36
        person.save()
        result = psh.rsync('./', dest)
        assert len(result) == 1
        assert person.obj_id in result


def test_rsync_history(historian, test_utils):
    """Test the that correct behaviour is implemented for syncing object histories"""
    car = mince_testing.Car(colour='red')
    car_id = historian.save(car)
    car.colour = 'blue'
    car.save()

    with test_utils.temporary_historian('test-rsync') as (uri, remote):
        dest = get_uri_with_objsys_path(uri, '/')
        result = psh.rsync('./', dest)
        assert car.obj_id in result

        # Check that, by default, history is not transferred
        results = list(remote.snapshots.records.find(obj_id=car_id))
        assert len(results) == 1
        assert results[0].version == 1  # Only the blue car is expected
