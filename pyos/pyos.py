import logging
import pprint
import typing

import mincepy

from . import dirs
from . import fmt
from . import lib
from . import nodes
from .dirs import PyosPath
from . import opts
from . import sopts
from . import utils
from .sopts import *  # pylint: disable=wildcard-import
from . import version

# pylint: disable=invalid-name

__all__ = ('pwd', 'cd', 'ls', 'load', 'save', 'cat', 'locate', 'mv', 'meta', 'rm', 'find',
           'history', 'tree', 'oid') + sopts.__all__

logger = logging.getLogger(__name__)


def pwd():
    """Return the current working directory"""
    return dirs.cwd()


def cd(path: dirs.PathSpec):
    path = PyosPath(path)
    if path.is_file():
        # Assume they just left out the slash
        path = path.to_dir()

    dirs.cd(path)


@opts.flag(-l)
@opts.flag(-d)
@opts.flag(-p)
def ls(*args) -> nodes.ResultsNode:
    """List the contents of a directory

    :type: restrict listing to a particular type
    """
    options = args[0]
    rest = list(args[1:])
    parsed = utils.parse_args(*rest)

    results = nodes.ResultsNode()
    if rest:
        for entry in parsed:
            if isinstance(entry, Exception):
                raise entry

            try:
                results.append(nodes.to_node(entry))
            except mincepy.NotFound as exc:
                logger.info(str(exc))
    else:
        results.append(nodes.to_node(dirs.cwd()))

    if not options.pop(sopts.d):
        for entry in results:
            if isinstance(entry, nodes.DirectoryNode):
                entry.expand(populate_objects=l in options)

        if len(results) == 1 and isinstance(results[0], nodes.DirectoryNode):
            sole_dir = results[0]
            new_results = nodes.ResultsNode(sole_dir.name)
            for result in tuple(sole_dir.children):
                result.parent = new_results

            results = new_results

    if options.pop(sopts.l):
        properties = ['loaded', 'type', 'version', 'mtime', 'name']
        if options.pop(sopts.p):
            properties.append('str')
        results.show(*properties, mode=nodes.TABLE_VIEW)
    else:
        results.show(mode=nodes.LIST_VIEW)

    return results


def load(*obj_or_ids) -> typing.Union[typing.Iterable[typing.Any], typing.Any]:
    """Load one or more objects"""
    _options, rest = opts.separate_opts(*obj_or_ids)
    to_load = ls(-d, *rest)

    loaded = []
    for node in to_load:
        try:
            loaded.append(node.obj)
        except Exception as exc:  # pylint: disable=broad-except
            loaded.append(exc)

    if len(loaded) == 1:
        return loaded[0]

    return loaded


@opts.flag(-f, help="Force - overwrite files with the same name")
def save(*args):
    """Save one or more objects"""
    options = args[0]
    objs = args[1:]

    if len(objs) > 1 and isinstance(objs[-1], (str, dirs.PyosPath)):
        # Extract the destination
        dest = PyosPath(objs[-1]).resolve()
        objs = objs[:-1]

        if len(objs) > 1 and dest.is_file():
            # Automatically convert to directory if there are many objects as they can't save
            # more than one with the same filename in the same folder!
            dest = dest.to_dir()

        save_args = tuple((obj, dest) for obj in objs)
        saved = lib.save_many(save_args, overwrite=-f in options)
    else:
        saved = lib.save_many(objs, overwrite=-f in options)

    if len(objs) == 1:
        return saved[0]

    return saved


def cat(*obj_or_ids):
    """Print the contents of one or more objects"""
    _options, rest = opts.separate_opts(*obj_or_ids)
    to_load = ls(-d, *rest)
    to_cat = load(to_load)

    for obj in to_cat:
        if isinstance(obj, Exception):
            print(obj)
        else:
            if isinstance(obj, mincepy.File):
                print(obj.read_text())
            else:
                pprint.pprint(fmt.obj_dict(obj))


def locate(*obj_or_ids) -> nodes.ResultsNode:
    """Locate the directory of or more objects"""
    _options, rest = opts.separate_opts(*obj_or_ids)
    to_locate = ls(-d, *rest)
    to_locate.show('abspath', mode=nodes.TABLE_VIEW)

    return to_locate


@opts.flag(-n, help="No clobber - don't overwrite if the same filename exists")
def mv(*args):  # pylint: disable=invalid-name
    """Take one or more files or directories with the final parameter being interpreted as
     destination"""
    options = args[0]
    rest = list(args[1:])
    assert len(rest) <= 2, "mv: missing destination"
    dest = dirs.PyosPath(rest.pop())
    if len(rest) > 1:
        # If there is more than one thing to move then we assume that dest is a directory
        dest = dest.to_dir()
    dest = dest.resolve()
    to_move = ls(-d, *rest)
    to_move.move(dest, overwrite=not options.pop(sopts.n))


def rm(*obj_or_ids):
    """Remove objects"""
    _options, rest = opts.separate_opts(*obj_or_ids)
    to_delete = ls(-d, *rest)
    for node in to_delete:
        node.delete()


@opts.flag(-s, "Set the metadata")
@opts.flag(-u, "Update the metadata")
def meta(*obj_or_ids, **updates):
    """Get, set or update the metadata on one or more objects"""
    options, rest = opts.separate_opts(*obj_or_ids)
    to_update = ls(-d, *rest)
    obj_ids = []
    for node in to_update:
        if isinstance(node, nodes.ObjectNode):
            obj_ids.append(node.obj_id)
        else:
            print("Can't set metadata on '{}'".format(node))

    if options.pop(-u, False):
        # In 'update' mode
        if not updates:
            return None
        lib.update_meta(*obj_ids, meta=updates)
    elif options.pop(-s, False):
        # In 'setting' mode
        if not updates:
            return None
        lib.set_meta(*obj_ids, meta=updates)
    else:
        # In 'getting' mode
        if updates:
            logging.warning("Keywords supplied to meta without -s/-u flags: %s", updates)
        metas = lib.get_meta(*obj_ids)
        if len(metas) == 1:
            return metas[0]

        return metas

    return None


def find(
        *starting_point,
        meta: dict = None,  # pylint: disable=redefined-outer-name
        state: dict = None,
        type=None,  # pylint: disable=redefined-builtin
        mindepth=0,
        maxdepth=-1) -> nodes.ResultsNode:
    _options, spoints = opts.separate_opts(*starting_point)
    if not spoints:
        spoints = (dirs.cwd(),)

    return lib.find(*spoints,
                    meta=meta,
                    state=state,
                    type=type,
                    mindepth=mindepth,
                    maxdepth=maxdepth)


def history(obj):
    hist = mincepy.get_historian()
    for entry in hist.history(obj):
        print(entry.ref)
        cat(entry.obj)
        print()


@opts.option(sopts.L)
def tree(options, *paths):
    """Get a tree representation of the given paths"""
    to_tree = ls(-d, *paths)
    level = options.pop(sopts.L, -1)
    # Fully expand all directories
    for dir_node in to_tree.directories:
        dir_node.expand(level)
    to_tree.show(mode=nodes.TREE_VIEW)
    return to_tree


def oid(*args):
    """Get the object id for one or more live objects"""
    _options, rest = opts.separate_opts(*args)
    hist = mincepy.get_historian()

    oids = []
    for obj in rest:
        try:
            oids.append(hist.get_obj_id(obj))
        except mincepy.NotFound:
            oids.append(None)

    if len(oids) == 1:
        return oids[0]

    return oids


def _mod() -> str:
    """Get the message of the day string"""
    return "Welcome to\n{}".format(version.BANNER)


print(_mod())
