# -*- coding: utf-8 -*-
"""
Low-level filesystem database commands.

The filesystem collection consists of entries corresponding to edges in a tree where the source
points to the parent directory and the destination points to the file or directory contained within it.
The edge also stores the name of the entry.

'name',
{
    'id': ...,
    'parent': id,
    'type': 'dir' or 'obj',
    'children':
    {
        'some child': {
            'id': ...',
            'parent':
        }
    }
}
"""
import datetime
from typing import Dict, List, Iterator, Optional, Tuple

import mincepy
import mincepy.mongo.db
import bson
import pymongo.errors

from pyos import exceptions
from . import constants
from . import database

COLLECTION = 'pyos_fs'

ROOT_ID = 'root'
ANCESTORS = 'ancestors'
DESCENDENTS = 'descendents'
RECORDS = 'records'

# Used temporarily during some aggregation stages
ENTRY = 'entry'

# The path type used by this low level module
Path = Tuple[str]


class Schema:
    """
    Schema for the edges in the filesystem collection
    """
    ID = '_id'  # pylint: disable=invalid-name
    NAME = 'name'
    PARENT = 'parent'
    TYPE = 'type'
    CTIME = 'ctime'
    MTIME = 'mtime'

    # Optional fields
    DESCENDENTS = DESCENDENTS
    DEPTH = 'depth'
    VER = 'ver'
    PATH_ENTRIES = 'path'

    # Values
    TYPE_DIR = 'dir'
    TYPE_OBJ = 'obj'

    @staticmethod
    def dir_dict(name: str, parent, dir_id=None) -> Dict:
        dtime = datetime.datetime.now()
        out = {
            Schema.ID: dir_id or bson.ObjectId(),
            Schema.NAME: name,
            Schema.PARENT: parent,
            Schema.TYPE: 'dir',
            Schema.CTIME: dtime,
            Schema.MTIME: dtime,
        }

        return out

    @staticmethod
    def obj_dict(obj_id, parent, name=None) -> Dict:
        return {
            Schema.ID: obj_id,
            Schema.NAME: name or str(obj_id),
            Schema.PARENT: parent,
            Schema.TYPE: 'obj'
        }


class Entry:

    def __init__(self):
        raise RuntimeError('Cannot instantiate')

    @staticmethod
    def is_dir(entry: Dict):
        return entry[Schema.TYPE] == Schema.TYPE_DIR

    @staticmethod
    def is_obj(entry: Dict):
        return entry[Schema.TYPE] == Schema.TYPE_OBJ

    @staticmethod
    def name(entry: Dict) -> str:
        return entry[Schema.NAME]

    @staticmethod
    def id(entry: Dict):  # pylint: disable=invalid-name
        return entry[Schema.ID]

    @staticmethod
    def type(entry: Dict) -> str:
        return entry[Schema.TYPE]

    @staticmethod
    def parent(entry: Dict):
        return entry[Schema.PARENT]

    @staticmethod
    def path_entries(entry: Dict) -> Optional[List[Dict]]:
        return entry.get(Schema.PATH_ENTRIES)

    @staticmethod
    def path(entry: Dict) -> Optional[Path]:
        path_entries = Entry.path_entries(entry)
        if path_entries is None:
            return None
        path_parts = _get_path_from_entries(path_entries)
        return path_parts + (Entry.name(entry),)

    @staticmethod
    def ctime(entry: Dict) -> datetime.datetime:
        return entry[Schema.CTIME]

    @staticmethod
    def mtime(entry: Dict) -> datetime.datetime:
        return entry[Schema.MTIME]

    @staticmethod
    def ver(entry: Dict) -> Optional[int]:
        return entry[Schema.VER]

    @staticmethod
    def depth(entry: Dict) -> Optional[int]:
        return entry.get(Schema.DEPTH, None)


ROOT = Schema.dir_dict(name='/', parent=None, dir_id=ROOT_ID)
ROOT_PATH = ('/',)


class FilesystemBuilder:

    def __init__(self, is_root=False):
        self._id = 'root' if is_root else bson.ObjectId()
        self._entries = {}

    def __getitem__(self, name: str) -> 'FilesystemBuilder':
        try:
            return self._entries[name]
        except KeyError:
            return self.add_dir(name)

    def add_dir(self, name: str):
        if name in self._entries:
            raise ValueError(f'Entry with name {name} already exists: {self._entries[name]}')

        subdir = FilesystemBuilder()
        self._entries[name] = subdir
        return subdir

    def add_obj(self, name: str, obj_id: bson.ObjectId):
        if name in self._entries:
            raise ValueError(f'Entry with name {name} already exists: {self._entries[name]}')

        self._entries[name] = obj_id
        return obj_id

    def create_edge_records(self) -> List[Dict]:
        return list(self.yield_edges())

    def yield_edges(self) -> Iterator[Dict]:
        for name, value in self._entries.items():
            if isinstance(value, FilesystemBuilder):
                yield Schema.dir_dict(name=name, parent=self._id, dir_id=value._id)  # pylint: disable=protected-access
                yield from value.yield_edges()
            else:
                yield Schema.obj_dict(obj_id=value, parent=self._id, name=name)  # pylint: disable=protected-access


def get_fs_collection(historian: mincepy.Historian = None):
    historian = historian or database.get_historian()
    archive: mincepy.mongo.MongoArchive = historian.archive
    return archive.database[constants.FILESYSTEM_COLLECTION]


# region query operations


def path_part_lookup(name: str) -> Dict:
    """Returns a MongoDB aggregate stage that does a graph lookup for a particular path part by matching the name"""
    return {
        '$graphLookup': {
            'from': 'pyos_fs',
            'startWith': f'${Schema.ID}',
            'connectFromField': Schema.ID,
            'connectToField': Schema.PARENT,
            'as': 'children',
            'maxDepth': 0,
            'restrictSearchWithMatch': {
                Schema.NAME: name
            }
        },
    }


def _path_lookup(path: Path, start_id=Entry.id(ROOT)) -> List[Dict]:
    """
    Returns a list of MongoDB aggregate stage operations that will match a filesystem path based on the passed parts
    """
    validate_path(path, absolute=start_id == Entry.id(ROOT))

    aggregate = [
        {
            '$match': {
                Schema.ID: start_id
            }
        },
        {
            '$addFields': {
                Schema.PATH_ENTRIES: ['$$ROOT']
            }
        },  # Add start document to the path
    ]
    for part in path[1:]:
        aggregate.extend([
            path_part_lookup(part),
            {
                '$replaceRoot': {
                    'newRoot': {
                        '$mergeObjects': [
                            {
                                '$arrayElemAt': ['$children', 0]
                            },
                            # Append the new child to the path
                            {
                                Schema.PATH_ENTRIES: {
                                    '$concatArrays': [
                                        f'$$ROOT.{Schema.PATH_ENTRIES}', '$$ROOT.children'
                                    ]
                                }
                            },
                        ]
                    }
                }
            },
        ])

    return aggregate


def _records_lookup() -> List[Dict]:
    """Look up object data records"""
    return [
        # Create a field for the object ID that will be used to lookup records but
        # only for objects, not directories
        {
            '$addFields': {
                mincepy.mongo.db.OBJ_ID: {
                    '$cond': {
                        'if': {
                            '$eq': [f'${Schema.TYPE}', Schema.TYPE_OBJ]
                        },
                        'then': f'${Schema.ID}',
                        'else': '$$REMOVE'
                    }
                }
            }
        },
        # Join any objects with their record in the mincePy data collection
        {
            '$lookup': {
                'from': mincepy.mongo.MongoArchive.DATA_COLLECTION,
                'localField': f'{mincepy.mongo.db.OBJ_ID}',
                'foreignField': mincepy.mongo.db.OBJ_ID,
                'as': RECORDS,
            }
        },
        # Don't keep object entries that have no records, these are spurious and should be cleaned up
        {
            '$match': {
                '$or': [{
                    Schema.TYPE: Schema.TYPE_DIR
                }, {
                    RECORDS: {
                        '$ne': []
                    }
                }]
            }
        },
        # Now keep certain fields that we're interested in
        {
            '$addFields': {
                Schema.CTIME: {
                    '$arrayElemAt': [f'$records.{mincepy.mongo.db.CREATION_TIME}', 0]
                },
                Schema.MTIME: {
                    '$arrayElemAt': [f'$records.{mincepy.mongo.db.SNAPSHOT_TIME}', 0]
                },
                Schema.VER: {
                    '$arrayElemAt': [f'$records.{mincepy.mongo.db.VERSION}', 0]
                },
                RECORDS: '$$REMOVE',
            }
        },
    ]


def _entries_lookup(*entry_id) -> List[Dict]:
    if not entry_id:
        return []
    if len(entry_id) == 1:
        return [{'$match': {Schema.ID: entry_id[0]}}]
    return [{'$match': {Schema.ID: {'$in': list(entry_id)}}}]


def _ancestors_lookup() -> List[Dict]:
    aggregate = [{
        '$graphLookup': {
            'from': COLLECTION,
            'startWith': f'${Schema.PARENT}',
            'connectFromField': Schema.PARENT,
            'connectToField': Schema.ID,
            'as': ANCESTORS,
            'depthField': Schema.DEPTH,
        }
    }]

    return aggregate


# endregion


def find_entry(
    path: Path,
    *,
    historian: mincepy.Historian = None,
) -> Optional[Dict]:
    """Find an entry in the filesystem collection based on the path"""

    aggregate = [*_path_lookup(path), *_records_lookup()]
    res = list(get_fs_collection(historian).aggregate(aggregate, allowDiskUse=True))
    if not res:
        return None

    assert len(res) == 1, \
        f'It should never happen that there is more than one match for a particular path but got: {res}'
    entry = res[0]

    if Schema.ID not in entry:
        # The path does not exist.  This code can be reached, for example, when all but the last path part exists
        return None

    return entry


def find_children(entry_id, *, historian: mincepy.Historian = None) -> Iterator[Dict]:
    aggregation = [{'$match': {Schema.PARENT: entry_id}}, *_records_lookup()]
    coll = get_fs_collection(historian)
    return coll.aggregate(aggregation, allowDiskUse=True)


def get_entry(
    entry_id,
    include_path=False,
    *,
    historian: mincepy.Historian = None,
) -> Dict:
    aggregate = [*_entries_lookup(entry_id), *_records_lookup()]

    if include_path:
        aggregate.extend(_ancestors_lookup())

    res = list(get_fs_collection(historian).aggregate(aggregate, allowDiskUse=True))
    if not res:
        return None

    assert len(res) == 1, \
        f'It should never happen that there is more than one match for a particular path but got: {res}'
    entry = res[0]

    if include_path:
        entry[ANCESTORS].sort(key=lambda ancestor: ancestor[Schema.DEPTH], reverse=True)
        entry[Schema.PATH_ENTRIES] = entry.pop(ANCESTORS)

    return entry


def find_path_entries(path: Path, historian: mincepy.Historian = None) -> List[Dict]:
    """Find all the entries along a path"""
    coll = get_fs_collection(historian=historian)
    res = list(coll.aggregate(_path_lookup(path)))

    if not res:
        raise exceptions.FileNotFoundError(path)

    assert len(res) == 1, \
        f'It should never happen that there is more than one match for a particular path but got: {res}'
    return res[0][Schema.PATH_ENTRIES]


def get_paths(*obj_id, historian: mincepy.Historian = None) -> Tuple[Path]:
    coll = get_fs_collection(historian=historian)
    aggregate = [*_entries_lookup(*obj_id), *_ancestors_lookup()]

    res = list(coll.aggregate(aggregate))

    paths: List[Path] = []
    for entry in res:
        # Have to reverse sort by depth because graph lookup doesn't guarantee order
        entry[ANCESTORS].sort(key=lambda ancestor: ancestor[Schema.DEPTH], reverse=True)
        path = list(ancestor[Schema.NAME] for ancestor in entry[ANCESTORS])
        path.append(entry[Schema.NAME])
        paths.append(tuple(path))

    return tuple(paths)


def set_path(obj_id,
             path: Path,
             upsert=True,
             exists_ok=True,
             historian: mincepy.Historian = None) -> Optional[Dict]:
    """Set the saved location of an object.

    :param path: the path to save the object at.  path[:-1] will be the absolute path to the directory while
        path[-1] will be the filename.  Note that the directory must already exist.
    """
    coll = get_fs_collection(historian=historian)

    dirpath, basename = path[:-1], path[-1]

    dir_entry = find_entry(dirpath, historian=historian)
    if not dir_entry:
        raise exceptions.FileNotFoundError(f'Directory not found: {dirpath}')

    new_entry = Schema.obj_dict(obj_id, parent=Entry.id(dir_entry), name=basename)
    if exists_ok:
        res = coll.replace_one({Schema.ID: obj_id}, new_entry, upsert=upsert)
        if res.modified_count != 1:
            # Didn't set path
            return None
    else:
        # Only insert if the object isn't already saved
        try:
            coll.insert_one(new_entry)
        except pymongo.errors.DuplicateKeyError:
            return None

    return new_entry


def set_paths(*obj_id_path, upsert=True, exists_ok=True, historian: mincepy.Historian = None):
    coll = get_fs_collection(historian=historian)
    ops = []
    results = []

    for obj_id, path in obj_id_path:
        dirpath, basename = path[:-1], path[-1]

        dir_entry = find_entry(dirpath, historian=historian)
        if not dir_entry:
            raise exceptions.FileNotFoundError(f'Directory not found: {dirpath}')

        new_entry = Schema.obj_dict(obj_id, parent=Entry.id(dir_entry), name=basename)
        results.append(new_entry)
        if exists_ok:
            ops.append(pymongo.ReplaceOne({Schema.ID: obj_id}, new_entry, upsert=upsert))
        else:
            # Only insert of the object isn't already saved
            ops.append(pymongo.InsertOne(new_entry))

    try:
        coll.bulk_write(ops)
    except pymongo.errors.BulkWriteError:
        pass

    return results


def make_dirs(path: Path, exists_ok=False, historian: mincepy.Historian = None):

    def already_exists():
        if not exists_ok:
            raise exceptions.FileExistsError(path)

    if path == ROOT_PATH:
        return already_exists()

    fs_coll = get_fs_collection(historian)
    aggregate = _path_lookup(path)
    res = list(fs_coll.aggregate(aggregate, allowDiskUse=True))
    if res:
        assert len(res) == 1, f'Expected a single result, got {res}'
        res = res[0]
    else:
        res = {Schema.PATH_ENTRIES: []}

    existing_path = res[Schema.PATH_ENTRIES]
    if len(existing_path) == len(path):
        return already_exists()

    # Make all the dirs that don't exist yet
    last_entry_id = existing_path[-1][Schema.ID]
    entries = []
    for name in path[len(existing_path):]:
        entry = Schema.dir_dict(name=name, parent=last_entry_id)
        entries.append(entry)
        last_entry_id = entry[Schema.ID]

    fs_coll.insert_many(entries)

    return None


def rename(path: Path, new_path: Path, historian: mincepy.Historian = None):
    coll = get_fs_collection(historian)
    entry = find_entry(path, historian=historian)  # DB HIT
    if not entry:
        raise exceptions.FileNotFoundError(f'File not found: {path}')

    new_dir_id = Entry.parent(entry)
    new_dir = new_path[:-1]
    if new_dir != path[:-1]:
        new_dir_entry = find_entry(new_dir, historian=historian)  # DB HIT
        if not new_dir_entry:
            raise exceptions.FileNotFoundError(f'File not found: {new_dir}')
        new_dir_id = Entry.id(new_dir_entry)

    new_doc = {
        Schema.ID: Entry.id(entry),
        Schema.NAME: new_path[-1],
        Schema.TYPE: Entry.type(entry),
        Schema.PARENT: new_dir_id
    }

    if Entry.is_dir(entry):
        # Renaming directory changes its modification time
        new_doc[Schema.MTIME] = datetime.datetime.now()

    try:
        coll.replace_one({'_id': new_doc[Schema.ID]}, new_doc, upsert=False)  # DB HIT
    except pymongo.errors.DuplicateKeyError as exc:
        # Trying to overwrite existing file with same name
        raise exceptions.FileExistsError(new_path) from exc


def rename_obj(obj_id, new_path: Path, historian: mincepy.Historian = None):
    # Find the entry corresponding to the new folder
    dirpath, basename = new_path[:-1], new_path[-1]

    new_dir = find_entry(dirpath, historian=historian)
    if new_dir is None:
        raise exceptions.FileNotFoundError(f'File not found: {dirpath}')

    # Update the object to be in the new location
    coll = get_fs_collection(historian=historian)
    coll.update_one({'_id': obj_id},
                    {'$set': {
                        Schema.PARENT: Entry.id(new_dir),
                        Schema.NAME: basename
                    }},
                    upsert=False)


def remove_obj(obj_id, historian: mincepy.Historian = None):
    coll = get_fs_collection(historian)
    coll.delete_one({Schema.ID: obj_id, Schema.TYPE: Schema.TYPE_OBJ})


def remove_objs(obj_ids: Tuple, historian: mincepy.Historian = None):
    coll = get_fs_collection(historian)
    coll.delete_many({Schema.ID: {'$in': list(obj_ids)}, Schema.TYPE: Schema.TYPE_OBJ})


def remove_dir(entry_id, recursive=False, historian: mincepy.Historian = None) -> Dict:
    entry = get_entry(entry_id, historian=historian)  # DB HIT
    if entry is None:
        raise exceptions.FileNotFoundError(entry_id)

    if Entry.is_obj(entry):
        raise exceptions.NotADirectoryError(entry_id)

    entry_ids = [entry_id]
    descendents = dict(iter_descendents(entry_id, historian=historian))
    if recursive:
        entry_ids.extend(descendents.values())
    elif descendents:
        raise exceptions.PyOSError(f'Directory not empty: {entry_id}')

    # Delete
    coll = get_fs_collection(historian)
    coll.delete_many({Schema.ID: {'$in': entry_ids}})  # DB HIT

    return entry


def validate_path(path: Path, absolute=True):
    forbidden_chars = ('/',)
    if not path:
        raise ValueError('Path not supplied')

    if absolute and path[0] != '/':
        raise ValueError(f"Expected absolute path, must start with '', for {path}")

    for idx, part in enumerate(path[1:]):
        if not (absolute and idx == 0) and part == '':
            raise ValueError(f'Path part cannot be empty, got: {path}')
        if any(char in part for char in forbidden_chars):
            raise ValueError(f"Path part cannot contain any of '{forbidden_chars}', got: {path}")


def iter_descendents(entry_id,
                     *,
                     of_type: str = None,
                     max_depth=None,
                     depth=0,
                     historian: mincepy.Historian = None):
    if of_type is not None and of_type not in (Schema.TYPE_DIR, Schema.TYPE_OBJ):
        raise ValueError(f'Invalid type filter: {of_type}')

    if max_depth is not None and depth >= max_depth:
        return
    for child in find_children(entry_id, historian=historian):
        if of_type is None or Entry.type(child) == of_type:
            yield depth + 1, child
        if Entry.is_dir(child):
            yield from iter_descendents(
                Entry.id(child),
                of_type=of_type,
                max_depth=max_depth,
                depth=depth + 1,
                historian=historian,
            )


def _get_path_from_entries(path_entries: List[Dict]) -> Path:
    return tuple(Entry.name(entry) for entry in path_entries)
