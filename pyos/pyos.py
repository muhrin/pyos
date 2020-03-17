from pathlib import PurePosixPath
import pprint
import tabulate
import typing

import mincepy

from . import dirs
from . import fmt
from . import lib
from . import opts
from . import sopts
from . import utils
from . import res
from .sopts import *
from .constants import DIR_KEY

# pylint: disable=invalid-name

__all__ = ('pwd', 'cd', 'ls', 'load', 'save', 'cat', 'locate', 'mv', 'meta', 'rm', 'find', 'rename',
           'ROOT', 'history') + sopts.__all__

ROOT = dirs.Directory('/')


def pwd():
    """Return the current working directory"""
    return dirs.cwd()


def cd(path: [str, PurePosixPath, dirs.Directory]):
    if isinstance(path, dirs.Directory):
        path = path.__path
    print(dirs.cd(path))


def ls(*args, type: typing.Type = None):
    """List the contents of a directory

    :type: restrict listing to a particular type
    """
    cwd = dirs.cwd()

    options, paths = opts.separate_opts(*args)

    objects, subdirs = dirs.get_contents(cwd)

    results = res.ObjIdList(objects.keys())
    results.show_types = True
    if l in options:
        results.show_loaded = True
        results.show_user = True
        results.show_mtime = True
        results.show_version = True

    return results

    # contents = lib.get_records(type=type, meta=meta)
    # objs = []
    # for record in contents:
    #     row = fmt.format_record(record, **format_flags)
    #     name = objects[record.obj_id]
    #     row.append(name if name else '')
    #     objs.append(row)
    #
    # show_dirs = not type and not meta
    #
    # table = []
    # if show_dirs:
    #     for subdir in sorted(subdirs):
    #         row = [''] * ncols
    #         row[0] = 'directory'
    #         row[-1] = subdir
    #         table.append(row)
    # table.extend(objs)
    #
    # print(tabulate.tabulate(table, tablefmt='plain'))


def load(*obj_or_ids):
    """Load one or more objects"""
    obj_ids = utils.flatten_obj_ids(*obj_or_ids)
    return mincepy.load(*obj_ids)


def save(*objs):
    """Save one or more objects"""
    return mincepy.save(*objs)


def cat(*obj_or_ids):
    """Print the contents of one or more objects"""
    hist = mincepy.get_historian()
    obj_or_ids = utils.flatten_obj_ids(*obj_or_ids)

    for obj_or_id in obj_or_ids:
        try:
            if hist.is_obj_id(obj_or_id) or isinstance(obj_or_id, str):
                obj = load(obj_or_id)
            else:
                obj = obj_or_id
        except TypeError as exc:
            print(exc)
        else:
            if isinstance(obj, mincepy.File):
                print(obj.read_text())
            else:
                pprint.pprint(fmt.obj_dict(obj))


def locate(*obj_or_ids) -> res.PathList:
    """Locate the directory of or more objects"""
    obj_ids = utils.flatten_obj_ids(*obj_or_ids)
    hist = mincepy.get_historian()
    path_list = res.PathList()

    results = hist.meta.find({'obj_id': {'$in': list(obj_ids)}})
    directories = {meta['obj_id']: meta.get(DIR_KEY, '/') for meta in results}

    for obj_id in obj_ids:
        path_list.append(directories[obj_id] / PurePosixPath(str(obj_id)))

    return path_list


def mv(*obj_or_ids):
    assert len(obj_or_ids) >= 2, "mv: missing destination"
    dest = PurePosixPath(obj_or_ids[-1])
    obj_ids = utils.flatten_obj_ids(*obj_or_ids[:-1])
    lib.mv(dest, obj_ids)
    print("OK")


def rm(*obj_or_ids):
    hist = mincepy.get_historian()
    for obj_or_id in utils.flatten_obj_ids(*obj_or_ids):
        try:
            hist.delete(obj_or_id)
        except mincepy.NotFound:
            print("rm: cannot remove '{}': no such object".format(obj_or_id))


def meta(*obj_or_ids, **meta):
    """Get or update the metadata on one or more objects"""
    obj_ids = utils.flatten_obj_ids(*obj_or_ids)

    if meta:
        # In 'setting' mode
        lib.update_meta(*obj_ids, meta=meta)
    else:
        # In 'getting' mode
        for meta in lib.get_meta(*obj_ids):
            return meta


def rename(obj_or_id, name: str):
    """Set the name of one or more objects."""
    obj_ids = utils.flatten_obj_ids(obj_or_id)
    lib.set_name(obj_ids, name)


def find(*args, **meta_filter):
    return lib.find(*args, **meta_filter)


def history(obj):
    hist = mincepy.get_historian()
    for entry in hist.history(obj):
        print(entry.ref)
        cat(entry.obj)
        print()
