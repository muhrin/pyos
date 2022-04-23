# -*- coding: utf-8 -*-
import math

import bson
import mincepy
import pytest

from pyos import os as pos
from pyos import db
from pyos.db import fs


def test_delete_outside_pyos(archive_uri):
    car = mincepy.testing.Car()
    car_id = db.save_one(car, 'my_car')
    assert pos.withdb.exists('my_car')

    hist = mincepy.connect(archive_uri, use_globally=False)
    hist.delete(car_id)

    assert not pos.withdb.exists('my_car')


def test_iter_children():
    black_car = mincepy.testing.Car(colour='black')
    pink_car = mincepy.testing.Car(colour='pink')
    mark = mincepy.testing.Person('mark', 23)
    dave = mincepy.testing.Person('dave', 54)
    pos.makedirs('subdir')

    # Save them all
    db.save_many((black_car, pink_car, mark, dave))

    # Now, make sure they are all children of the current directory
    fs_entry = fs.find_entry(pos.withdb.to_fs_path(pos.getcwd()))
    entry_id = fs.Entry.id(fs_entry)
    children = list(fs.iter_children(entry_id))

    assert len(children) == 5
    ids = tuple(map(fs.Entry.id, children))
    assert black_car.obj_id in ids
    assert pink_car.obj_id in ids
    assert mark.obj_id in ids
    assert dave.obj_id in ids
    assert fs.Entry.id(fs.find_entry(pos.withdb.to_fs_path('./subdir'))) in ids

    # Now check that filtering works
    children = list(fs.iter_children(entry_id, obj_filter=mincepy.testing.Car.colour == 'black'))
    assert len(children) == 2
    ids = tuple(map(fs.Entry.id, children))
    assert black_car.obj_id in ids

    children = list(
        fs.iter_children(entry_id,
                         obj_filter=mincepy.DataRecord.type_id == mincepy.testing.Car.TYPE_ID))
    assert len(children) == 3

    # Check that meta filtering works
    db.set_meta(black_car, meta=dict(reg='1234'))
    db.set_meta(pink_car, meta=dict(reg='1466'))

    children = tuple(
        fs.iter_children(
            entry_id,
            type=fs.Schema.TYPE_OBJ,  # Only find objects (not directories)
            meta_filter={'reg': '1234'}))
    assert len(children) == 1
    assert fs.Entry.id(children[0]) == black_car.obj_id


def test_iter_descendents():
    start_dir = pos.getcwd()

    pos.makedirs('a/b/c')
    for dirname in ('a', 'b', 'c'):
        pos.chdir(dirname)

        mincepy.testing.Car(colour='black').save()
        mincepy.testing.Person('mark', 23).save()

    root_id = fs.Entry.id(fs.find_entry(pos.withdb.to_fs_path(start_dir)))
    descendents = tuple(fs.iter_descendents(root_id))
    assert len(descendents) == 9

    # Now check that filtering works
    descendents = tuple(
        fs.iter_descendents(root_id, obj_filter=mincepy.testing.Car.colour == 'black'))
    assert len(descendents) == 6


@pytest.mark.skip()
def test_delete_many_entries():
    """Test that deleting a large number of entries works.  If this is done in a single MongoDB delete_many command it
    will exceed the 16MB document limit so check that the command still works even in such a case"""
    obj_id_bytes = 12
    # Calculate the number of object ids it would take to burst the 16MB limit
    num_entries = math.ceil(16 * 1024 * 1024 / obj_id_bytes)

    fake_objects = (bson.ObjectId() for _ in range(num_entries))
    for obj_id in fake_objects:
        db.fs.insert_obj(obj_id, ('/', str(obj_id)))

    db.fs._delete_entries(*fake_objects)  # pylint: disable=protected-access
