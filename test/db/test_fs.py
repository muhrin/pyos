# -*- coding: utf-8 -*-
import mincepy

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
    children = list(fs.iter_children(fs.Entry.id(fs_entry)))

    assert len(children) == 5
    ids = tuple(map(fs.Entry.id, children))
    assert black_car.obj_id in ids
    assert pink_car.obj_id in ids
    assert mark.obj_id in ids
    assert dave.obj_id in ids
    assert fs.Entry.id(fs.find_entry(pos.withdb.to_fs_path('./subdir'))) in ids

    # Now check that filtering works
    children = list(
        fs.iter_children(fs.Entry.id(fs_entry), obj_filter=mincepy.testing.Car.colour == 'black'))
    assert len(children) == 2
    ids = tuple(map(fs.Entry.id, children))
    assert black_car.obj_id in ids

    children = list(
        fs.iter_children(fs.Entry.id(fs_entry),
                         obj_filter=mincepy.DataRecord.type_id == mincepy.testing.Car.TYPE_ID))
    assert len(children) == 3


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
