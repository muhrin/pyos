# -*- coding: utf-8 -*-
"""
Low-level filesystem database commands.

The filesystem collection consists of entries corresponding to edges in a tree where the source
points to the parent directory and the destination points to the file or directory contained within it.
The edge also stores the name of the entry.
"""
import abc
import collections
import datetime
from typing import Dict, List, Iterator, Optional, Tuple, Iterable

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
Path = Tuple[str, ...]


class Schema:
    """
    Schema for the edges in the filesystem collection
    """
    ID = '_id'  # pylint: disable=invalid-name
    NAME = 'name'
    PARENT = 'parent'
    TYPE = 'type'
    CTIME = 'ctime'  # Creation time of the entry
    UTIME = 'utime'  # Last update time of the entry (e.g. name change or move)

    # Optional fields
    STIME = mincepy.SNAPSHOT_TIME  # Last snapshot time of the object (i.e. last time it was changed)
    DESCENDENTS = DESCENDENTS
    DEPTH = 'depth'
    VER = mincepy.VERSION
    TYPE_ID = mincepy.TYPE_ID
    PATH_ENTRIES = 'path_entries'
    PATH = 'path'

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
            Schema.STIME: dtime,
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
    def set_parent(entry_id, parent_id, historian: mincepy.Historian):
        coll = get_fs_collection(historian)
        coll.update_one({Schema.ID: entry_id}, {Schema.PARENT: parent_id})

    @staticmethod
    def path_entries(entry: Dict) -> Optional[List[Dict]]:
        return entry.get(Schema.PATH_ENTRIES)

    @staticmethod
    def path(entry: Dict) -> Optional[Path]:
        if Schema.PATH in entry:
            return entry[Schema.PATH]

        path_entries = Entry.path_entries(entry)
        if path_entries is None:
            return None

        path_parts = _get_path_from_entries(path_entries)
        return path_parts + (Entry.name(entry),)

    @staticmethod
    def ctime(entry: Dict) -> datetime.datetime:
        return entry[Schema.CTIME]

    @staticmethod
    def stime(entry: Dict) -> datetime.datetime:
        """Get the snapshot time of the object"""
        return entry[Schema.STIME]

    @staticmethod
    def ver(entry: Dict) -> Optional[int]:
        """Get the version number of the object"""
        return entry[Schema.VER]

    @staticmethod
    def type_id(entry: Dict) -> Optional:
        return entry[Schema.TYPE_ID]

    @staticmethod
    def depth(entry: Dict) -> Optional[int]:
        return entry.get(Schema.DEPTH, None)


ROOT = Schema.dir_dict(name='/', parent=None, dir_id=ROOT_ID)
ROOT_PATH = ('/',)

FIELD_MAP = {
    mincepy.TYPE_ID: Schema.TYPE_ID,
    mincepy.VERSION: Schema.VER,
    mincepy.CREATION_TIME: Schema.CTIME,
    mincepy.SNAPSHOT_TIME: Schema.STIME,
}


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


class EntriesCache:

    def __init__(self, historian: mincepy.Historian):
        self._hist = historian or database.get_historian()
        self._entry_ids = {}
        self._paths = {}
        self._path_entries = {}

    @property
    def historian(self) -> mincepy.Historian:
        return self._hist

    def get_entry(self, id_or_path) -> Dict:
        if isinstance(id_or_path, tuple):
            return self.get_entry_from_path(id_or_path)

        # Assume it's an entry id
        return self.get_entry_from_id(id_or_path)

    def get_entry_from_path(self, path: Path) -> Dict:
        if not isinstance(path, tuple):
            raise TypeError(f'Expected tuple, got {path.__class__.__name__}')

        try:
            return self._paths[path]
        except KeyError:
            entry = find_entry(path, historian=self._hist)
            if entry is not None:
                # Cache the entry
                self._paths[path] = entry
                self._entry_ids[Entry.id(entry)] = entry

            return entry

    def get_entry_from_id(self, entry_id) -> Dict:
        try:
            return self._entry_ids[entry_id]
        except KeyError:
            entry = get_entry(entry_id, historian=self._hist)
            if entry is not None:
                # Cache the entry
                self._entry_ids[Entry.id(entry)] = entry

            return entry

    def get_path_entries(self, path: Path) -> List[Dict]:
        try:
            return self._path_entries[path]
        except KeyError:
            entries = find_path_entries(path, self._hist)
            for entry in entries:
                self._entry_ids[Entry.id(entry)] = entry
            self._path_entries[path] = entries
            return entries


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
        # Join any objects with their record in the mincePy data collection
        {
            '$lookup': {
                'from': mincepy.mongo.MongoArchive.DATA_COLLECTION,
                'localField': f'{Schema.ID}',
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
                Schema.STIME: {
                    '$arrayElemAt': [f'$records.{mincepy.mongo.db.SNAPSHOT_TIME}', 0]
                },
                Schema.VER: {
                    '$arrayElemAt': [f'$records.{mincepy.mongo.db.VERSION}', 0]
                },
                Schema.TYPE_ID: {
                    '$arrayElemAt': [f'$records.{mincepy.mongo.db.TYPE_ID}', 0]
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
    aggregate = _path_lookup(path)
    historian = historian or database.get_historian()

    res = list(get_fs_collection(historian).aggregate(aggregate, allowDiskUse=True))
    if not res:
        return None

    assert len(res) == 1, \
        f'It should never happen that there is more than one match for a particular path but got: {res}'
    entry = res[0]

    if Schema.ID not in entry:
        # The path does not exist.  This code can be reached, for example, when all but the last path part exists
        return None

    if Entry.is_obj(entry):
        try:
            # pylint: disable=protected-access
            data_entry = tuple(
                historian.records.find(obj_id=Entry.id(entry))._project(*FIELD_MAP.keys()))[0]
        except IndexError:
            return None
        else:
            _copy_fields(entry, data_entry)

    return entry


def get_entry(
    entry_id,
    include_path=False,
    *,
    historian: mincepy.Historian = None,
) -> Dict:
    aggregate = _entries_lookup(entry_id)

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

    if Entry.is_obj(entry):
        try:
            # pylint: disable=protected-access
            data_entry = tuple(
                historian.records.find(obj_id=Entry.id(entry))._project(*FIELD_MAP.keys()))[0]
        except IndexError:
            return None
        else:
            _copy_fields(entry, data_entry)

    return entry


def find_path_entries(path: Path, historian: mincepy.Historian = None) -> List[Dict]:
    """Find all filesystem the entries along a path"""
    coll = get_fs_collection(historian=historian)
    res = list(coll.aggregate(_path_lookup(path)))

    if not res:
        raise exceptions.FileNotFoundError(path)

    assert len(res) == 1, \
        f'It should never happen that there is more than one match for a particular path but got: {res}'
    return res[0][Schema.PATH_ENTRIES]


def get_paths(*obj_id, historian: mincepy.Historian = None) -> Tuple[Path]:
    if not obj_id:
        return tuple()

    coll = get_fs_collection(historian=historian)
    aggregate = [*_entries_lookup(*obj_id), *_ancestors_lookup()]

    res = list(coll.aggregate(aggregate))

    paths = {}
    for entry in res:
        # Have to reverse sort by depth because graph lookup doesn't guarantee order
        entry[ANCESTORS].sort(key=lambda ancestor: ancestor[Schema.DEPTH], reverse=True)
        path = list(ancestor[Schema.NAME] for ancestor in entry[ANCESTORS])
        path.append(entry[Schema.NAME])
        paths[Entry.id(entry)] = path

    retval = []
    for oid in obj_id:
        retval.append(paths.get(oid, None))

    return tuple(retval)


def set_obj_path(obj_id,
                 new_path: Path,
                 historian: mincepy.Historian = None,
                 cache: EntriesCache = None):
    """
    Set the path for a filesystem entry

    :param parent: the path to save the object at.  path[:-1] will be the absolute path to the directory while
        path[-1] will be the filename.  Note that the directory must already exist.
    """
    cache = cache or EntriesCache(historian)
    instruction = SetObjPath(obj_id, new_path)
    ops = instruction.get_ops(cache)

    coll = get_fs_collection(historian=historian)
    try:
        coll.bulk_write(ops)
    except pymongo.errors.BulkWriteError as exc:
        # Ask the instruction to handle the error
        instruction.handle_exception(exc.details['writeErrors'][0])


class Instruction(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_ops(self, cache: EntriesCache):
        """Get the bulk operations needed to carry out this instruction"""

    def handle_exception(self, error: Dict):
        raise exceptions.PyOSError(error)


class SetObjPath(Instruction):
    """Change the name or location of an existing filesystem entry"""

    def __init__(self, obj_id, new_path: Path, only_new=False):
        if obj_id is None:
            raise ValueError('Must supply entry id')

        self.entry_id = obj_id
        self.new_path = new_path
        self.only_new = only_new

    def get_ops(self, cache: EntriesCache) -> List:
        return SetObjPath._set_path_operations(cache, self.entry_id, self.new_path, self.only_new)

    @staticmethod
    def _set_path_operations(
        cache: EntriesCache,
        obj_id,
        new_path: Path,
        only_new=False,
    ) -> List:
        # Find out where they want to put it
        parent, basename = new_path[:-1], new_path[-1]
        parent_entry = cache.get_entry_from_path(parent)  # Possible DB HIT

        if parent_entry is None:
            raise exceptions.FileNotFoundError(parent)
        if not Entry.is_dir(parent_entry):
            raise exceptions.NotADirectoryError(parent)

        parent_id = Entry.id(parent_entry)

        time_now = datetime.datetime.now()
        if only_new:
            # Only set the path if the object isn't already in the filesystem
            update = {'$setOnInsert': Schema.obj_dict(obj_id, parent_id, name=basename)}
        else:
            # Set the new path whether or not it exists
            update = {
                '$set': {
                    Schema.PARENT: parent_id,
                    Schema.NAME: basename,
                    Schema.UTIME: time_now,
                },
                '$setOnInsert': {
                    Schema.TYPE: Schema.TYPE_OBJ,
                    Schema.CTIME: time_now
                }
            }

        return [
            pymongo.UpdateOne({
                Schema.ID: obj_id,
                Schema.TYPE: Schema.TYPE_OBJ
            },
                              update,
                              upsert=True)
        ]

    def handle_exception(self, error: Dict):
        if error['code'] == 11000:
            raise exceptions.FileExistsError(self.new_path)

        super().handle_exception(error)


class Rename(Instruction):

    def __init__(self, src_id, dest_path):
        self.src_id = src_id
        self.dest_path = dest_path

    def get_ops(self, cache: EntriesCache):
        return Rename.rename_operations(cache, self.src_id, self.dest_path)

    @staticmethod
    def rename_operations(cache: EntriesCache, src_id, dest_path):
        dest_dir, dest_name = dest_path[:-1], dest_path[-1]

        parent_entry = cache.get_entry_from_path(dest_dir)  # Possible DB HIT
        if not Entry.is_dir(parent_entry):
            raise exceptions.NotADirectoryError(dest_dir)

        return [
            pymongo.UpdateOne(
                {Schema.ID: src_id},
                {'$set': {
                    Schema.PARENT: Entry.id(parent_entry),
                    Schema.NAME: dest_name
                }})
        ]

    def handle_exception(self, error: Dict):
        if error['code'] == 11000:
            raise exceptions.FileExistsError()


def execute_instructions(instructions: Iterable[Instruction], historian: mincepy.Historian = None):
    cache = EntriesCache(historian)
    ops = []
    for instruction in instructions:
        ops.extend(instruction.get_ops(cache))

    if ops:
        get_fs_collection(historian).bulk_write(ops)


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


def rename(
    src: Path = None,
    dest: Path = None,
    src_id=None,
    historian: mincepy.Historian = None,
    cache: EntriesCache = None,
):
    """Rename a filesystem entry"""
    cache = cache or EntriesCache(historian)

    if src_id is None:
        if src is None:
            raise ValueError('Have to supply source or source id')
        src_entry = cache.get_entry_from_path(src)
        if src_entry is None:
            raise exceptions.FileExistsError(src)
        src_id = Entry.id(src_entry)

    # Find the entry corresponding to the new folder
    dirpath, basename = dest[:-1], dest[-1]

    new_dir = cache.get_entry_from_path(dirpath)
    if new_dir is None:
        raise exceptions.FileNotFoundError(f'File not found: {dirpath}')

    # Update the object to be in the new location
    coll = get_fs_collection(historian=historian)
    try:
        res = coll.update_one({Schema.ID: src_id},
                              {'$set': {
                                  Schema.PARENT: Entry.id(new_dir),
                                  Schema.NAME: basename
                              }},
                              upsert=False)
    except pymongo.errors.DuplicateKeyError:
        raise exceptions.FileExistsError(dest) from None
    else:
        if res.modified_count == 1:
            return True

        return False


RemoveResult = collections.namedtuple('RemoveResult', 'dirs_removed objs_removed')


def remove_obj(obj_id, historian: mincepy.Historian = None) -> bool:
    """Remove a single object entry"""
    coll = get_fs_collection(historian)
    res = coll.delete_one({Schema.ID: obj_id, Schema.TYPE: Schema.TYPE_OBJ})
    if res.deleted_count == 1:
        return True

    return False


def remove_objs(obj_ids: Tuple, historian: mincepy.Historian = None) -> int:
    """Remove many object entries"""
    coll = get_fs_collection(historian)
    res = coll.delete_many({Schema.ID: {'$in': list(obj_ids)}, Schema.TYPE: Schema.TYPE_OBJ})
    return res.deleted_count


def remove_dir(entry_id, recursive=False, historian: mincepy.Historian = None) -> RemoveResult:
    entry = get_entry(entry_id, historian=historian)  # DB HIT
    if entry is None:
        raise exceptions.FileNotFoundError(entry_id)

    if Entry.is_obj(entry):
        raise exceptions.NotADirectoryError(entry_id)

    to_delete = []
    result = RemoveResult([], [])

    # Check for descendents
    descendents = tuple(iter_descendents(entry_id, historian=historian))
    if recursive:
        for descendent in descendents:
            descendent_id = Entry.id(descendent)
            if Entry.is_obj(descendent):
                result.objs_removed.append(descendent_id)
            else:
                result.dirs_removed.append(descendent_id)

            to_delete.append(descendent_id)
    elif descendents:
        raise exceptions.PyOSError(f'Directory not empty: {entry_id}')

    # Delete the given directory id last
    to_delete.append(entry_id)
    result.dirs_removed.append(entry_id)

    # Delete
    _delete_entries(*to_delete, historian=historian)  # DB HIT

    return result


def _delete_entries(*entry_id, historian: mincepy.Historian = None):
    """Delete entries from the filesystem collection.  No checks are done, just does a raw delete."""
    delete_ops = list(pymongo.DeleteOne({Schema.ID: fsid}) for fsid in entry_id)
    return get_fs_collection(historian).bulk_write(delete_ops)  # DB HIT


def insert_obj(obj_id, dest: Path, historian: mincepy.Historian = None, cache: EntriesCache = None):
    cache = cache or EntriesCache(historian)
    dirpath, name = dest[:-1], dest[-1]
    dest_entry = cache.get_entry_from_path(dirpath)

    if dest_entry is None:
        raise exceptions.FileNotFoundError(f'File not found: {dirpath}')

    coll = get_fs_collection(cache.historian)
    try:
        coll.insert_one(Schema.obj_dict(obj_id, Entry.id(dest_entry), name))
    except pymongo.errors.DuplicateKeyError:
        raise exceptions.FileExistsError(dest) from None


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


def iter_children(
    entry_id,
    *,
    type: str = None,  # pylint: disable=redefined-builtin
    obj_filter: mincepy.Expr = None,
    obj_type=None,
    meta_filter=None,
    historian: mincepy.Historian = None,
    batch_size=1024,
) -> Iterator[Dict]:
    """Given a filesystem directory id iterate over all of its children"""
    # pylint: disable=too-many-branches
    if type is not None and type not in (Schema.TYPE_DIR, Schema.TYPE_OBJ):
        raise ValueError(f'Invalid type filter: {type}')

    historian = historian or database.get_historian()
    coll = get_fs_collection(historian)

    find_filter = {Schema.PARENT: entry_id}
    if type is not None:
        find_filter[Schema.TYPE] = type

    res = coll.find(find_filter, batch_size=batch_size)
    has_more = True
    while has_more:
        found = []
        objects = {}
        for _ in range(batch_size):
            try:
                entry = res.next()
            except StopIteration:
                has_more = False
                break
            else:
                # Only need to check objects, directories are always returned directly
                if Entry.is_obj(entry):
                    objects[Entry.id(entry)] = entry
                else:
                    found.append(entry)

        if objects:
            # Now check that the objects still exist and extract some additional info
            # pylint: disable=protected-access

            # Create the filter to be used for finding records
            data_filter = mincepy.DataRecord.obj_id.in_(*objects.keys())
            if obj_filter:
                data_filter &= obj_filter

            record_find = historian.records.find(data_filter, obj_type=obj_type, meta=meta_filter)
            records = {
                entry[mincepy.OBJ_ID]: entry
                for entry in record_find._project(mincepy.OBJ_ID, *FIELD_MAP.keys())
            }

            for obj_id, entry in objects.items():
                try:
                    data_entry = records[obj_id]
                except KeyError:
                    # Pass this one, doesn't match the filter
                    pass
                else:
                    # Copy over the additional fields we want
                    _copy_fields(entry, data_entry)
                    found.append(entry)

        yield from found


def iter_descendents(
        entry_id,
        *,
        type: str = None,  # pylint: disable=redefined-builtin
        obj_filter: mincepy.Expr = None,
        obj_type=None,
        meta_filter=None,
        max_depth=None,
        depth=0,
        path: Path = (),
        historian: mincepy.Historian = None):
    if type is not None and type not in (Schema.TYPE_DIR, Schema.TYPE_OBJ):
        raise ValueError(f'Invalid type filter: {type}')

    if max_depth is not None and depth >= max_depth:
        return
    for child in iter_children(entry_id,
                               obj_filter=obj_filter,
                               obj_type=obj_type,
                               meta_filter=meta_filter,
                               historian=historian):
        child_path = path + (Entry.name(child),)
        if type is None or Entry.type(child) == type:
            child[Schema.DEPTH] = depth + 1
            child[Schema.PATH] = child_path
            yield child

        if Entry.is_dir(child):
            yield from iter_descendents(
                Entry.id(child),
                type=type,
                obj_filter=obj_filter,
                obj_type=obj_type,
                meta_filter=meta_filter,
                max_depth=max_depth,
                depth=depth + 1,
                path=child_path,
                historian=historian,
            )


def _copy_fields(fs_entry: Dict, mincepy_entry: Dict):
    """Copy over fields from mincepy data records to our filesystem entry dictionary format"""
    for mince_field, fs_field in FIELD_MAP.items():
        fs_entry[fs_field] = mincepy_entry[mince_field]


def _consume_batch(cursor, batch_size: int) -> List:
    return [entry for entry, _ in zip(cursor, range(batch_size))]


def _get_path_from_entries(path_entries: List[Dict]) -> Path:
    return tuple(Entry.name(entry) for entry in path_entries)
