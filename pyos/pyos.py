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
from . import sopts
from .sopts import *

# pylint: disable=invalid-name

__all__ = ('pwd', 'cd', 'ls', 'load', 'save', 'cat', 'locate', 'mv', 'meta', 'rm', 'find',
           'history', 'tree') + sopts.__all__


def pwd():
    """Return the current working directory"""
    return dirs.cwd()


def cd(path: dirs.PathSpec):
    path = PyosPath(path)
    if path.is_file():
        # Assume they just left out the slash
        path = path.to_dir()

    dirs.cd(path)


def ls(*args, _type: typing.Type = None) -> nodes.ResultsNode:
    """List the contents of a directory

    :type: restrict listing to a particular type
    """
    options, rest = opts.separate_opts(*args)
    parsed = utils.parse_args(*rest)

    results = nodes.ResultsNode()
    if parsed:
        for entry in parsed:
            if isinstance(entry, Exception):
                raise entry
            results.append(nodes.to_node(entry))
    else:
        results.append(nodes.to_node(dirs.cwd()))

    if not options.pop(sopts.d):
        for entry in results:
            if isinstance(entry, nodes.DirectoryNode):
                entry.expand()

        if len(results) == 1 and isinstance(results[0], nodes.DirectoryNode):
            sole_dir = results[0]
            new_results = nodes.ResultsNode(sole_dir.name)
            for result in tuple(sole_dir.children):
                result.parent = new_results

            results = new_results

    if options.pop(sopts.l):
        results.show('loaded', 'type', 'creator', 'version', 'mtime', 'name', mode=nodes.TABLE_VIEW)
    else:
        results.show(mode=nodes.LIST_VIEW)

    return results


def load(*obj_or_ids) -> typing.Iterable:
    """Load one or more objects"""
    _options, rest = opts.separate_opts(*obj_or_ids)
    to_load = ls(-d, *rest)

    loaded = []
    for node in to_load:
        try:
            loaded.append(mincepy.load(node.obj_id))
        except Exception as exc:  # pylint: disable=broad-except
            loaded.append(exc)

    if len(loaded) == 1:
        return loaded[0]

    return loaded


def save(*objs):
    """Save one or more objects"""

    if len(objs) > 1 and isinstance(objs[-1], (str, dirs.PyosPath)):
        # Extract the destination
        dest = PyosPath(objs[-1]).resolve()
        objs = objs[:-1]

        if len(objs) > 1 and dest.is_file():
            # Automatically convert to directory if there are many objects as they can't save
            # more than one with the same filename in the same folder!
            dest = dest.to_dir()

        return lib.save(objs, [dest] * len(objs))

    return lib.save(objs)


def cat(*obj_or_ids):
    """Print the contents of one or more objects"""
    _options, rest = opts.separate_opts(*obj_or_ids)
    to_cat = load(*rest)

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


def mv(*args):  # pylint: disable=invalid-name
    """Take one or more files or directories with the final parameter being interpreted as
     destination"""
    _options, rest = opts.separate_opts(*args)
    assert len(rest) <= 2, "mv: missing destination"
    dest = dirs.PyosPath(rest.pop())
    if len(rest) > 1:
        # If there is more than one thing to move then we assume that dest is a directory
        dest = dest.to_dir()
    dest = dest.resolve()
    to_move = ls(*rest[:-1])
    to_move.move(dest)


def rm(*obj_or_ids):
    _options, rest = opts.separate_opts(*obj_or_ids)
    to_delete = ls(-d, *rest)
    for node in to_delete:
        node.delete()


def meta(*obj_or_ids, **updates):
    """Get or update the metadata on one or more objects"""
    _options, rest = opts.separate_opts(*obj_or_ids)
    to_update = ls(-d, *rest)
    obj_ids = []
    for node in to_update:
        if isinstance(node, nodes.ObjectNode):
            obj_ids.append(node.obj_id)
        else:
            print("Can't set metadata on '{}'".format(node))

    if updates:
        # In 'setting' mode
        lib.update_meta(*obj_ids, meta=updates)
    else:
        # In 'getting' mode
        metas = lib.get_meta(*obj_ids)
        if len(metas) == 1:
            return metas[0]

        return metas

    return None


def find(*args, **meta_filter):
    return lib.find(*args, **meta_filter)


def history(obj):
    hist = mincepy.get_historian()
    for entry in hist.history(obj):
        print(entry.ref)
        cat(entry.obj)
        print()


def tree(*obj_or_ids):
    options, rest = opts.separate_opts(*obj_or_ids)
    to_tree = ls(-d, *rest)
    level = options.pop(sopts.L, -1)
    # Fully expand all directories
    for dir_node in to_tree.directories:
        dir_node.expand(level)
    to_tree.show(mode=nodes.TREE_VIEW)
    return to_tree
