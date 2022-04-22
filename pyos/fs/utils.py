# -*- coding: utf-8 -*-
import collections
import concurrent.futures

import mincepy

import pyos.db.fs
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
         obj_filter: mincepy.Expr = None,
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

    obj_ids = collections.defaultdict(set)

    def populate_object_ids(path):
        # Find the filesystem entry we're looking for
        start_fs_path = os.withdb.to_fs_path(path)
        entry = db.fs.find_entry(start_fs_path, historian=historian)

        if db.fs.Entry.is_obj(entry):
            if mindepth == 0:
                obj_ids[db.fs.Entry.id(entry)].add(path)
        else:
            for descendent in db.fs.iter_descendents(db.fs.Entry.id(entry),
                                                     max_depth=maxdepth if maxdepth != -1 else None,
                                                     path=start_fs_path,
                                                     historian=historian):
                depth = pyos.db.fs.Entry.depth(descendent)
                if db.fs.Entry.is_obj(descendent) and depth >= mindepth:
                    descendent_path = db.fs.Entry.path(descendent)
                    obj_ids[db.fs.Entry.id(descendent)].add(os.withdb.from_fs_path(descendent_path))

    # Can use as many executors as paths because this operation is limited by the server and not the
    # python code
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(starting_point)) as executor:
        executor.map(populate_object_ids, starting_point)

    hist = historian or db.get_historian()
    entries = {}

    # Get the records that match both the record and metadata criteria
    filter_expr = mincepy.DataRecord.obj_id.in_(*obj_ids.keys())
    if obj_filter is not None:
        filter_expr &= obj_filter
    for record in hist.records.find(obj_filter, obj_type=type, state=state, meta=meta):
        entries.setdefault(record.obj_id, {})['record'] = record

    results = nodes.ResultsNode()
    results.show('relpath')

    for obj_id, entry in entries.items():
        for path in obj_ids.get(obj_id, set()):
            # Create the filesystem node
            node = nodes.ObjectNode(obj_id, path=path, record=entry.get('record', None))
            results.append(node)

    return results
