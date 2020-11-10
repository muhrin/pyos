# -*- coding: utf-8 -*-
"""The move command"""
import argparse
import collections
from typing import Optional, Tuple, List, Callable

import cmd2
import mincepy
import pymongo.errors
import yarl

import pyos
from pyos import fs
from pyos import db
from pyos import os
from pyos.psh import completion

META_UPDATE = 'update'
META_OVERWRITE = 'overwrite'


@pyos.psh_lib.command(pass_options=True)
def rsync(options, *args, progress=False, history=False, meta=None):  # pylint: disable=invalid-name, unused-argument
    """Remote sync.

    Synchronise the source and destination.  The src and destination can be
    either local or remote path.
    Remote paths should be specified with as a URI string containing the
    remote server path, database name followed by the path e.g.:

    mongodb://localhost/my_db/my_folder/my_sub_folder/

    rsync uses similar path syntax to mv, e.g.:

    Files as input:
    rsync ('a', 'mongodb://localhost/db/b/')  - copy file 'a' into folder 'b/' on localhost
    rsync ('a', 'mongodb://localhost/db/b')   - copy file a to b on localhost

    Folders as input:
    rsync ('a/', 'mongodb://localhost/db/b/') - copy folder 'a/' into folder 'b/' on localhost
    becoming 'b/a/'
    rsync ('a/', 'mongodb://localhost/db/b')  - copy folder 'a/' to be called 'b' on localhost
    having path 'b/'

    Multiple inputs:
    rsync (*src, 'mongodb://localhost/db/d')  - copy all supplied *src paths to 'd/' on localhost
    rsync (*src, 'mongodb://localhost/db/d/') - same as above

    For now, files will not be overwritten.
    """
    if len(args) < 2:
        raise ValueError('rsync: missing destination')

    args = list(args)
    dest = args.pop()

    src_url, src_paths = _get_sources(*args)
    dest_url, dest_path = _parse_location(dest)
    try:
        # 1. Set up the source
        if src_url:
            src = db.connect(src_url, use_globally=False)
        else:
            src = db.get_historian()

        # 2. Set up the destination
        if dest_url:
            dest = db.connect(dest_url, use_globally=False)
        else:
            dest = db.get_historian()
    except pymongo.errors.OperationFailure as exc:
        print("Error trying to connect with src '{} {}', and dest '{} {}'".format(
            src_url, src_paths, dest_url, dest_path))
        print(exc)
        return 1
    else:
        # 3. Perform historian merge on objects
        def show_progress(prog, _merge_results):
            if progress:
                print(prog)

        result = pyos.fs.ResultsNode()
        for src_path in src_paths:
            sync_result = _sync_objects(src,
                                        src_path,
                                        dest,
                                        dest_path,
                                        history=history,
                                        meta=meta,
                                        progress_cb=show_progress)
            for entry in sync_result.merged:
                result.append(pyos.fs.to_node(entry.obj_id, historian=dest))

        return result


def _sync_objects(src: mincepy.Historian,
                  src_path: str,
                  dest: mincepy.Historian,
                  dest_path: str,
                  history=False,
                  meta=None,
                  progress_cb: Callable = None):
    """Synchronise objects from a given source at the given path, to the destination at the given path


    """
    # Get the object ids at the source path
    path = os.path.abspath(src_path)
    obj_ids = tuple(entry.obj_id for entry in fs.find(path, historian=src).objects)  # DB HIT

    # This is the set of objects we will be syncing
    src_collection = src.snapshots if history else src.objects

    sync_set = src_collection.find(mincepy.DataRecord.obj_id.in_(*obj_ids))

    def batch_merged(progress, result):
        """Callback called when a batch si merged"""
        # Now we have to put the newly transferred objects into the correct path
        # first get the paths for each of the merged objects
        all_obj_ids = set(sid.obj_id for sid in result.all)

        # Dictionary to store the metadatas we need to set at the dest
        dest_metas = collections.defaultdict(dict)

        # Get all the metadata at the source
        src_metas = dict(src.meta.find({}, obj_id=all_obj_ids))

        if meta is not None:
            # We're being asked to merge metadata at the source so update our dictionary
            dest_metas.update(src_metas)

        # Now, figure out where we should store the objects
        for obj_id, src_meta in src_metas.items():
            if src_meta is None:
                continue

            obj_path = db.path_from_meta_entry(obj_id, src_meta)
            relpath = os.path.relpath(obj_path, src_path)
            if relpath.startswith(os.pardir):
                # This object will saved using its abspath
                new_paths = obj_path
            else:
                new_paths = os.path.join(dest_path, relpath)

            dest_metas[obj_id].update(db.path_to_meta_dict(new_paths))

        # Now update all the metadata dictionaries
        if dest_metas:
            if meta == META_UPDATE:
                dest.meta.update_many(dest_metas)
            else:
                dest.meta.set_many(dest_metas)

        if progress_cb is not None:
            progress_cb(progress, result)

    return dest.merge(sync_set, progress_callback=batch_merged, batch_size=256)


def _get_sources(*src) -> Tuple[Optional[str], List[str]]:
    paths = []
    url = None
    for entry in src:
        this_url, this_path = _parse_location(entry)
        if this_url:
            if url is None:
                url = this_url
            else:
                if url != this_url:
                    raise ValueError(
                        'Cannot have two different remote sources, got {} and {}'.format(
                            url, this_url))
        else:
            paths.append(this_path)

    return url, paths


def _parse_location(location: str) -> Tuple[Optional[str], str]:
    url = yarl.URL(location)
    if not url.scheme:
        return None, location

    # Skip the first entry as it is empty after splitting, and the second which is the database name
    path_parts = url.path.split('/')
    url = url.with_path(''.join(path_parts[:2])).with_query(url.query)
    fs_path = '/' + '/'.join(path_parts[2:])  # The filesystem path

    # Get rid of filesystem path part
    return str(url), fs_path


class Rsync(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument('--history',
                        action='store_true',
                        default=False,
                        help='synchronise object history as well as current versions')
    parser.add_argument('--progress',
                        action='store_true',
                        default=False,
                        help='show progress during transfer')
    parser.add_argument('--meta',
                        choices=[META_UPDATE, META_OVERWRITE],
                        help="""Synchronise metadata as well as objects.

                        Options are:
                            update      - perform a dictionary update with any existing metadata
                            overwrite   - replace any existing metadata with that from SRC
                            """)
    parser.add_argument('path', nargs='*', type=str, completer_method=completion.path_complete)

    @cmd2.with_argparser(parser)
    def do_rsync(self, args):  # pylint: disable=no-self-use
        command = rsync
        progress = args.progress
        history = args.history
        meta = args.meta
        print(command(*args.path, progress=progress, history=history, meta=meta))
