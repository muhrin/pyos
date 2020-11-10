# -*- coding: utf-8 -*-
import mincepy.testing as mince_testing
import yarl

from pyos import psh
from pyos import os
from pyos import fs


def ensure_at_path(*objs, path, historian):
    at_destination = fs.find(path, historian=historian)
    not_found = tuple(obj for obj in objs if obj not in at_destination)
    assert not not_found


def get_uri_with_objsys_path(archive_uri: str, path: str):
    if path.startswith(os.sep):
        path = path[1:]
    return str(yarl.URL(archive_uri) / path)


def test_rsync_basic(historian, test_utils):
    car = mince_testing.Car()
    person = mince_testing.Person('martin', 35, car=car)
    historian.save(car, person)

    with test_utils.temporary_historian('test-rsync') as (uri, remote):
        dest_path = '/home/'
        dest = get_uri_with_objsys_path(uri, dest_path)
        result = psh.rsync('./', dest)
        assert car.obj_id in result
        assert person.obj_id in result

        ensure_at_path(car.obj_id, person.obj_id, path=dest_path, historian=remote)

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
        dest_path = '/home/'
        dest = get_uri_with_objsys_path(uri, dest_path)
        result = psh.rsync('./', dest)
        assert car.obj_id in result
        ensure_at_path(car.obj_id, path=dest_path, historian=remote)

        # Check that, by default, history is not transferred
        results = list(remote.snapshots.records.find(obj_id=car_id))
        assert len(results) == 1
        assert results[0].version == 1  # Only the blue car is expected


def test_shell_rsync(historian, test_utils, pyos_shell):
    car = mince_testing.Car()
    person = mince_testing.Person('martin', 35, car=car)
    car_id, person_id = historian.save(car, person)

    with test_utils.temporary_historian('test-rsync') as (uri, remote):
        dest_path = '/home/'
        dest = get_uri_with_objsys_path(uri, dest_path)
        res = pyos_shell.app_cmd('rsync ./ {}'.format(dest))
        assert not res.stderr
        assert remote.objects.find(obj_id=[car_id, person_id]).count() == 2
        ensure_at_path(car_id, person_id, path=dest_path, historian=remote)

        # Make a mutation and see if it is synced
        person.age = 36
        person.save()
        res = pyos_shell.app_cmd('rsync ./ {}'.format(dest))
        assert not res.stderr
        assert remote.objects.records.find(obj_id=person_id, version=1).count() == 1


def test_rsync_meta(historian, test_utils):
    local = historian
    car = mince_testing.Car()
    person = mince_testing.Person('martin', 35, car=car)
    car_id, person_id = local.save(car, person)

    car_meta = {'ref': 'VD123'}
    person_meta = {'birthplace': 'toronto'}
    car.update_meta(car_meta)
    person.update_meta(person_meta)

    with test_utils.temporary_historian('test-rsync') as (uri, remote):
        dest_path = '/home/'
        dest = get_uri_with_objsys_path(uri, dest_path)
        result = psh.rsync('./', dest, meta='overwrite')
        assert car_id in result
        assert person_id in result

        # Now, check that the meta has been transferred
        assert check_meta_contains(car_meta, remote.meta.get(car.obj_id))
        assert check_meta_contains(person_meta, remote.meta.get(person.obj_id))

        # Now, change the metadata and sync again
        car_meta = {'age': 12}
        car.set_meta(car_meta)
        psh.rsync('./', dest, meta='overwrite')
        assert check_meta_contains(car_meta, remote.meta.get(car.obj_id))

        # Now try update
        combined = car_meta.copy()
        car_meta = {'sold': True}
        combined.update(car_meta)
        car.set_meta(car_meta)
        psh.rsync('./', dest, meta='update')
        assert check_meta_contains(combined, remote.meta.get(car.obj_id))


def check_meta_contains(template: dict, meta: dict):
    for key, value in template.items():
        try:
            if meta[key] != value:
                return False
        except KeyError:
            return False
    return True
