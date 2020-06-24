import mincepy

from pyos import os
from pyos import db
from pyos import pathlib

from . import nodes

__all__ = ('find',)


# pylint: disable=redefined-builtin
def find(*starting_point,
         meta: dict = None,
         state: dict = None,
         type=None,
         mindepth=0,
         maxdepth=-1) -> nodes.ResultsNode:
    """
    Find objects matching the given criteria

    :param starting_point: the starting points for the search, if not supplied defaults to '/'
    :param meta: filter criteria for the metadata
    :param state: filter criteria for the object's saved state
    :param type: restrict the search to this type (can be a tuple of types)
    :param mindepth: the minimum depth from the starting point(s) to search in
    :param maxdepth: the maximum depth from the starting point(s) to search in
    :return: results node
    """
    if not starting_point:
        starting_point = (os.getcwd(),)
    meta = (meta or {}).copy()
    state = (state or {}).copy()

    # Converting starting points to abspaths
    spoints = [str(pathlib.PurePath(path).to_dir().resolve()) for path in starting_point]

    # Add the directory search criteria to the meta search
    subdirs_query = (db.queries.subdirs(point, mindepth, maxdepth) for point in spoints)
    meta.update(db.queries.or_(*subdirs_query))

    hist = db.get_historian()

    # Find the metadata
    metas = dict(hist.meta.find(meta))
    records = {}
    if metas and (type is not None or state is not None):
        # Further restrict the match
        obj_id_filter = mincepy.q.in_(*metas.keys())
        for record in hist.find_records(obj_id=obj_id_filter, obj_type=type, state=state):
            records[record.obj_id] = record

    results = nodes.ResultsNode()
    results.show('relpath')

    for obj_id, record in records.items():
        node = nodes.ObjectNode(obj_id, record=record, meta=metas[obj_id])
        results.append(node)

    return results