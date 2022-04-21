# -*- coding: utf-8 -*-
import mincepy.mongo
import pymongo.database

from . import constants
from . import migrations


def get_db_version(database: pymongo.database.Database):
    """Get the version number of the database schema"""
    if constants.PYOS_COLLECTION not in database.list_collection_names():
        return 0

    coll = database[constants.PYOS_COLLECTION]
    return coll.find_one({'_id': 'settings'}).get(constants.SETTINGS_VERSION, 0)


def set_db_version(database: pymongo.database.Database, version: int):
    """Set the version number of the database schema"""
    coll = database[constants.PYOS_COLLECTION]
    coll.update_one({'_id': 'settings'}, {'$set': {
        constants.SETTINGS_VERSION: version
    }},
                    upsert=True)


def get_source_version() -> int:
    """Get the current version number of the schema used in this source code.
    This is equal to the total number of migrations"""
    return len(migrations.MIGRATIONS)


def ensure_up_to_date(historian: mincepy.Historian):
    """Ensure that the database schema is up-to-date, performing migrations to bring it up to
    date if it is not."""
    archive: mincepy.mongo.MongoArchive = historian.archive
    db = archive.database  # pylint: disable=invalid-name
    db_version = get_db_version(db)

    if db_version < get_source_version():
        # Apply the migrations that need to be applied one by one
        for migration in migrations.MIGRATIONS[db_version:]:
            migration(historian)
            db_version += 1
            set_db_version(db, db_version)

        return True

    return False
