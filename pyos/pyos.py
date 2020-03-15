from pathlib import PurePosixPath
import pprint
import tabulate
import typing

import mincepy

from . import dirs
from . import format
from . import lib
from . import utils

# pylint: disable=invalid-name

__all__ = 'pwd', 'cwd', 'cd', 'ls', 'load', 'cat', 'locate', 'mv', 'meta', 'rm', 'f', 'rename', \
          'ROOT'

lib.init()

ROOT = dirs.Directory('/')


def pwd():
    """Return the current working directory"""
    print(dirs.cwd())


def cwd() -> dirs.Directory:
    return dirs.Directory(dirs.cwd())


def cd(path: [str, PurePosixPath, dirs.Directory]):
    if isinstance(path, dirs.Directory):
        path = path.__path
    print(dirs.cd(path))


def ls(*opts, type: typing.Type = None, **meta):
    """List the contents of a directory

    :type: restrict listing to a particular type
    """
    cwd = dirs.cwd()

    format_flags = {}
    ncols = 4

    identifiers = []
    for opt in opts:
        if isinstance(opt, str) and opt.strip() == '-l':
            format_flags['user'] = True
            format_flags['ctime'] = True
            format_flags['version'] = True
            ncols = 7
        else:
            # Assume it's an identifier
            identifiers.append(opt)

    objects, subdirs = dirs.get_contents(cwd)
    contents = lib.get_records(type=type, meta=meta)
    objs = []
    for record in contents:
        row = format.format_record(record, **format_flags)
        name = objects[record.obj_id]
        row.append(name if name else '')
        objs.append(row)

    show_dirs = not type and not meta

    table = []
    if show_dirs:
        for subdir in sorted(subdirs):
            row = [''] * ncols
            row[0] = 'directory'
            row[-1] = subdir
            table.append(row)
    table.extend(objs)

    print(tabulate.tabulate(table, tablefmt='plain'))


def load(*obj_or_ids):
    """Load or more objects"""
    obj_ids = utils.expand_to_obj_ids(obj_or_ids)
    return mincepy.load(*obj_ids)


def cat(*obj_or_ids):
    """Print the contents of one or more objects"""
    hist = mincepy.get_historian()
    obj_or_ids = utils.expand_to_obj_ids(obj_or_ids)

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
                pprint.pprint(format.obj_dict(obj))


def locate(*obj_or_ids):
    """Locate the directory of or more objects"""
    obj_ids = utils.expand_to_obj_ids(obj_or_ids)
    for directory in lib.locate(obj_ids):
        print(directory)


def mv(*obj_or_ids):
    assert len(obj_or_ids) >= 2, "mv: missing destination"
    dest = PurePosixPath(obj_or_ids[-1])
    obj_ids = utils.expand_to_obj_ids(obj_or_ids[:-1])
    lib.mv(dest, obj_ids)
    print("OK")


def rm(*obj_or_ids):
    hist = mincepy.get_historian()
    for obj_or_id in utils.expand_to_obj_ids(obj_or_ids):
        try:
            hist.delete(obj_or_id)
        except mincepy.NotFound:
            print("rm: cannot remove '{}': no such object".format(obj_or_id))


def meta(*obj_or_ids, **meta):
    """Get or update the metadata on one or more objects"""
    obj_ids = utils.expand_to_obj_ids(obj_or_ids)

    if meta:
        # In 'setting' mode
        lib.update_meta(*obj_ids, meta=meta)
    else:
        # In 'getting' mode
        for meta in lib.get_meta(*obj_ids):
            pprint.pprint(meta)


def rename(obj_or_id, name: str):
    """Set the name of one or more objects."""
    obj_ids = utils.get_obj_id(obj_or_id)
    lib.set_name(obj_ids, name)


def f(*starting_point, **meta_filter):
    return lib.find_ids(*starting_point, **meta_filter)


def history(obj):
    hist = mincepy.get_historian()
    for entry in hist.history(obj):
        print(entry.ref)
        cat(entry.obj)
        print()
