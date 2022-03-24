# -*- coding: utf-8 -*-
import concurrent.futures

import mincepy

from pyos import os
from pyos import db
from . import nodes

__all__ = ('find',)


# pylint: disable=redefined-builtin
def find(*starting_point,
         meta: dict = None,
         state: dict = None,
         type=None,
         mindepth=0,
         maxdepth=-1,
         historian: mincepy.Historian = None) -> nodes.ResultsNode:
    """
    Find objects matching the given criteria

    :param starting_point: the starting points for the search, if not supplied defaults to '/'
    :param meta: filter criteria for the metadata
    :param state: filter criteria for the object's saved state
    :param type: restrict the search to this type (can be a tuple of types)
    :param mindepth: the minimum depth from the starting point(s) to search in
    :param maxdepth: the maximum depth from the starting point(s) to search in
    :param historian: the Historian to use
    :return: results node
    """
    if not starting_point:
        starting_point = (os.getcwd(),)

    meta = (meta or {}).copy()
    state = (state or {}).copy()

    obj_ids = set()

    def populate_object_ids(path):
        entry = db.fs.find_entry(os.withdb.to_fs_path(path), historian=historian)
        if db.fs.Entry.is_obj(entry):
            if mindepth == 0:
                obj_ids.add(db.fs.Entry.id(entry))
        else:
            for depth, descendent in db.fs.iter_descendents(
                    db.fs.Entry.id(entry),
                    max_depth=maxdepth if maxdepth != -1 else None,
                    historian=historian):
                if db.fs.Entry.is_obj(descendent) and depth >= mindepth:
                    obj_ids.add(db.fs.Entry.id(descendent))

    # Can use as many executors as paths because this operation is limited by the server and not the
    # python code
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(starting_point)) as executor:
        executor.map(populate_object_ids, starting_point)

    match = mincepy.DataRecord.obj_id.in_(*obj_ids)

    hist = historian or db.get_historian()
    entries = {}

    # Get the records that match both the record and metadata criteria
    for record in hist.records.find(match, obj_type=type, state=state, meta=meta):
        entries.setdefault(record.obj_id, {})['record'] = record

    # Now get the metadata for those objects
    for obj_id, meta_dict in hist.meta.find(filter={}, obj_id=list(entries.keys())):
        entries.setdefault(obj_id, {})['meta'] = meta_dict

    results = nodes.ResultsNode()
    results.show('relpath')

    for obj_id, entry in entries.items():
        node = nodes.ObjectNode(obj_id,
                                record=entry.get('record', None),
                                meta=entry.get('meta', None))
        results.append(node)

    return results
