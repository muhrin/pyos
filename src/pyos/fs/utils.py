from typing import TYPE_CHECKING, Optional

import mincepy
import mincepy.frontend

from . import nodes
from .. import _globals, db, os
from .. import results as results_

if TYPE_CHECKING:
    import pyos

__all__ = ("find",)


# pylint: disable=redefined-builtin
def find(
    *starting_point,
    meta: Optional[dict] = None,
    state: Optional[dict] = None,
    type=None,
    obj_filter: mincepy.Expr = None,
    mindepth=0,
    maxdepth=-1,
    session: Optional["pyos.Session"] = None,
) -> nodes.FrozenResultsNode:
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

    expr = mincepy.Empty()
    if obj_filter:
        expr = obj_filter
    if state:
        expr &= mincepy.build_expr(mincepy.frontend.flatten_filter("state", state)[0])

    def yield_results():
        for path in starting_point:
            for matching in _iter_matching(
                path,
                obj_filter=expr,
                obj_type=type,
                meta_filter=meta,
                mindepth=mindepth,
                maxdepth=maxdepth,
                session=session,
            ):
                descendent_path = db.fs.Entry.path(matching)
                path = os.withdb.from_fs_path(descendent_path)
                yield nodes.ObjectNode(db.fs.Entry.id(matching), path)

    results = nodes.FrozenResultsNode(results_.CachingResults(yield_results()))
    results.show("relpath", mode=nodes.SINGLE_COLUMN_VIEW)
    return results


def _iter_matching(
    path,
    obj_filter,
    obj_type,
    meta_filter,
    mindepth: int,
    maxdepth: int,
    session: Optional["pyos.Session"],
):
    # Find the filesystem entry we're looking for
    start_fs_path = os.withdb.to_fs_path(path)
    entry = db.fs.find_entry(start_fs_path, session=session)
    entry_id = db.fs.Entry.id(entry)

    if db.fs.Entry.is_obj(entry):
        if mindepth == 0:
            entry[db.fs.Schema.PATH] = path
            yield entry
    else:
        yield from _iter_descendents(
            entry_id,
            start_fs_path,
            obj_filter=obj_filter,
            obj_type=obj_type,
            meta_filter=meta_filter,
            mindepth=mindepth,
            maxdepth=maxdepth,
            session=session,
        )


def _iter_descendents(
    dir_fsid,
    start_path,
    obj_filter=None,
    obj_type=None,
    meta_filter=None,
    mindepth=0,
    maxdepth=-1,
    session: Optional["pyos.Session"] = None,
):
    # Find the filesystem entry we're looking for
    session = session if session is not None else _globals.get_global_session()

    objects_iter = db.fs.iter_descendents(
        dir_fsid,
        type=db.fs.Schema.TYPE_OBJ,  # Only interested in objects
        obj_filter=obj_filter,
        obj_type=obj_type,
        meta_filter=meta_filter,
        max_depth=maxdepth if maxdepth != -1 else None,
        path=start_path,
        session=session,
    )

    for descendent in objects_iter:
        depth = db.fs.Entry.depth(descendent)
        if depth >= mindepth:
            yield descendent
