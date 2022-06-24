# -*- coding: utf-8 -*-
import mincepy
import mincepy.mongo

from pyos import config
from . import constants


def initial(historian: mincepy.Historian):
    """
    Version 0.

    Initial migration.  Make sure meta indices are there."""

    # Make sure the indexes are there
    historian.meta.create_index([
        (config.NAME_KEY, mincepy.ASCENDING),
        (config.DIR_KEY, mincepy.ASCENDING),
    ],
                                unique=True,
                                where_exist=True)
    historian.meta.create_index(config.NAME_KEY, unique=False, where_exist=True)
    historian.meta.create_index(config.DIR_KEY, unique=False, where_exist=True)


def add_pyos_collections(historian: mincepy.Historian):
    """
    Version 1.

    Migrates from using metadata to store filesystem information to a dedicated MongoDB collection
    """
    from . import fs

    archive: mincepy.mongo.MongoArchive = historian.archive
    db = archive.database  # pylint: disable=invalid-name

    schema_version = getattr(archive, 'schema_version', 0)

    if schema_version >= 2:
        meta_entries = archive.data_collection.aggregate([{
            '$match': {
                'meta': {
                    '$exists': True
                }
            }
        }, {
            '$replaceRoot': {
                'newRoot': '$meta'
            }
        }])
    else:
        metas = db[archive.META_COLLECTION]
        meta_entries = metas.find({config.DIR_KEY: {'$exists': True}})

    # Find all the objects that have a directory key
    root = fs.FilesystemBuilder(is_root=True)
    for meta in meta_entries:
        obj_id = meta['_id']
        directory = root
        for entry in meta[config.DIR_KEY].split('/')[1:-1]:
            directory = directory[entry]
        directory.add_obj(meta.get(config.NAME_KEY, str(obj_id)), obj_id)

    records = root.create_edge_records()

    fs_collection = db[constants.FILESYSTEM_COLLECTION]
    fs_collection.create_index(fs.Schema.PARENT, unique=False)
    # Create a joint, unique, index on the source and name meaning that there cannot be two entries
    # with the same name in any directory
    fs_collection.create_index([(fs.Schema.PARENT, mincepy.ASCENDING),
                                (fs.Schema.NAME, mincepy.ASCENDING)],
                               unique=True)

    fs_collection.replace_one({'_id': fs.ROOT_ID}, fs.ROOT, upsert=True)

    if records:
        fs_collection.insert_many(records)


# Ordered list of migrations
MIGRATIONS = (
    initial,
    add_pyos_collections,
)
