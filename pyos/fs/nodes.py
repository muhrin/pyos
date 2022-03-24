# -*- coding: utf-8 -*-
import abc
import collections.abc
import copy
import functools
import sys
from typing import Dict, Sequence, Optional

import anytree
import columnize
import tabulate

import mincepy

from pyos import db
from pyos import exceptions
from pyos import fmt
from pyos import os
from pyos import pathlib
from pyos import results
from pyos import utils

__all__ = ('BaseNode', 'DirectoryNode', 'ObjectNode', 'ResultsNode', 'to_node', 'TABLE_VIEW',
           'LIST_VIEW', 'TREE_VIEW')

LIST_VIEW = 'list'
TREE_VIEW = 'tree'
TABLE_VIEW = 'table'

CHILDREN = 'children'


class BaseNode(collections.abc.Sequence,
               anytree.NodeMixin,
               results.BaseResults,
               metaclass=abc.ABCMeta):
    """Base node for the object system in pyos"""

    def __init__(self, name: str, parent=None, historian: mincepy.Historian = None):
        super().__init__()
        self._name = name
        self.parent = parent
        self._hist = historian or db.get_historian()

    def __getitem__(self, item):
        if isinstance(item, (int, slice)):
            return self.children.__getitem__(item)
        if isinstance(item, str):
            for child in self.children:
                if child.name == item:
                    return child
            raise ValueError(f'No child has name {item}')

        raise TypeError(f"Got unsupported item type '{item.__class__.__name__}'")

    def __len__(self):
        return self.children.__len__()

    @property
    def name(self):
        return self._name

    def delete(self):
        """Delete this node and any descendents"""
        for child in self.children:
            child.delete()

    def move(self, dest: os.PathSpec, overwrite=False):
        """Move this object (with any children) into the directory given by dest

        :param dest: the destination to move the node to
        :param overwrite: overwrite if exists
        """
        dest = pathlib.Path(dest).to_dir()
        for child in self.children:
            child.move(dest, overwrite)


class FilesystemNode(BaseNode):
    """Base node for representing an object in the virtual filesystem"""

    # Either give me:
    # * object id
    # * entry dict
    # * path

    def __init__(self,
                 path: os.PathSpec = None,
                 parent: BaseNode = None,
                 entry_id=None,
                 entry: Dict = None,
                 *,
                 historian: mincepy.Historian = None):
        """
        :param path: the path this node represents
        :param parent: parent node
        """
        historian = historian or db.get_historian()

        # First we have to try and get a filesystem entry
        if entry is None:
            if entry_id is not None:
                entry = db.fs.get_entry(entry_id, include_path=True, historian=historian)  # DB HIT
                if entry is None:
                    raise exceptions.FileNotFoundError(entry_id)
            elif path is not None:
                entry = db.fs.find_entry(os.withdb.to_fs_path(path), historian=historian)  # DB HIT
                if entry is None:
                    raise exceptions.FileNotFoundError(path)
            else:
                raise ValueError('Must supply filesystem entry, an entry id or a path')

        if path is None:
            entry_path = db.fs.Entry.path(entry)
            if entry_path is None:
                path = os.withdb.from_fs_path(db.fs.get_paths(db.fs.Entry.id(entry)))[0]
            else:
                path = os.withdb.from_fs_path(entry_path)

        path = pathlib.Path(path).resolve()
        super().__init__(path.name, parent, historian=historian)
        self._abspath = path
        self._entry = entry
        self._hist = historian

    @property
    def abspath(self) -> 'pathlib.Path':
        return self._abspath

    @abc.abstractmethod
    def rename(self, new_name: str):
        """Rename this filesystem node"""

    @property
    def entry_id(self):
        return db.fs.Entry.id(self._entry)


class ContainerNode(BaseNode):
    """A node that contains children that can be either directory nodes or object nodes"""

    def __contains__(self, item):
        # pylint: disable=too-many-nested-blocks, too-many-branches, too-many-return-statements
        if isinstance(item, pathlib.PurePath):
            path = pathlib.Path(item)
            if path.is_absolute():
                if path.is_dir():
                    # It's a directory
                    for node in self.directories:
                        if path == node.abspath:
                            return True
                else:
                    # It's a filename
                    for node in self.objects:
                        if path == node.abspath:
                            return True

                # Always check within directories
                for node in self.directories:
                    if path in node:
                        return True
            else:
                # It's relative
                parts = path.parts
                if len(parts) > 1:
                    subpath = pathlib.PurePath(''.join(parts[1:]))

                    # Check subdirs
                    for node in self.directories:
                        if node.abspath.name == parts[0] and subpath in node:
                            return True
                else:
                    if path.is_dir():
                        # It's a directory
                        for node in self.directories:
                            if node.abspath.name == parts[0]:
                                return True
                    else:
                        # It's a filename
                        for obj in self.objects:
                            if obj.abspath.name == parts[0]:
                                return True

            return False

        if self._hist.is_obj_id(item):
            for node in self.objects:
                if item == node.obj_id:
                    return True

            return False

        return False

    def __getitem__(self, item):
        items = super().__getitem__(item)
        if isinstance(item, slice):
            res = ResultsNode()
            for entry in items:
                res.append(copy.copy(entry))
            return res

        return items

    @property
    def directories(self):
        return filter(lambda node: isinstance(node, DirectoryNode), self.children)

    @property
    def objects(self):
        return filter(lambda node: isinstance(node, ObjectNode), self.children)


class DirectoryNode(ContainerNode, FilesystemNode):
    """A node representing an object system directory"""

    def __init__(self,
                 path: os.PathSpec,
                 parent: BaseNode = None,
                 entry: Dict = None,
                 *,
                 historian: mincepy.Historian = None):
        path = pathlib.Path(path)
        super().__init__(path=path.resolve(), parent=parent, entry=entry, historian=historian)
        if not db.fs.Entry.is_dir(self._entry):
            raise exceptions.NotADirectoryError(path)

    def __repr__(self):
        rep = []
        for pre, _, node in anytree.RenderTree(self):
            rep.append(f'{pre}{node.name}')
        return '\n'.join(rep)

    def __copy__(self):
        """Create a copy with no parent"""
        dir_node = DirectoryNode(self.abspath, self._entry)
        dir_node.children = [copy.copy(child) for child in self.children]
        return dir_node

    def __contains__(self, item):
        # Have to expand if we're not already otherwise contains could incorrectly fail
        if not self.children:
            self.expand()
        return super().__contains__(item)

    def __getitem__(self, item):
        # Have to expand if we're not already already otherwise contains could incorrectly fail
        if not self.children:
            self.expand()
        return super().__getitem__(item)

    def _invalidate_cache(self):
        self.children = []

    def expand(self, depth=1, populate_objects=False):  # pylint: disable=unused-argument
        """Populate the children with what is currently in the database

        :param depth: expand to the given depth, 0 means no expansion, 1 means my child nodes, etc
        :param populate_objects: if True objects will have their records fetched immediately (as
            opposed to lazily when needed).  This gives a large speedup when the client knows that
            the all or most of the details of the child objects will be needed as they can be
            fetched in one call.
        """
        self.children = []
        if depth == 0:
            return

        if depth > 0:
            child_expand_depth = depth - 1
        else:
            child_expand_depth = -1

        if CHILDREN not in self._entry:
            self._entry[CHILDREN] = list(db.fs.find_children(self.entry_id, historian=self._hist))

        added = []
        for descendent in self._entry[CHILDREN]:
            path = (self._abspath / db.fs.Entry.name(descendent))
            if db.fs.Entry.is_dir(descendent):
                dir_node = DirectoryNode(
                    path,
                    # parent=self,
                    entry=descendent,
                    historian=self._hist)
                added.append(dir_node)
                if abs(child_expand_depth) > 0:
                    dir_node.expand(child_expand_depth)
            else:
                obj_node = ObjectNode(
                    db.fs.Entry.id(descendent),
                    path=path,
                    # parent=self,
                    entry=descendent,
                    historian=self._hist)
                added.append(obj_node)

        self.children = added

    def delete(self):
        # 1. Find all the objects at or below this directory
        res = db.fs.iter_descendents(self.entry_id,
                                     of_type=db.fs.Schema.TYPE_OBJ,
                                     historian=self._hist)
        obj_ids = [db.fs.Entry.id(entry) for _, entry in res]

        # 2. Delete them
        if obj_ids:
            self._hist.delete(*obj_ids)

        # 3. Delete myself
        db.fs.remove_dir(self.entry_id, recursive=True, historian=self._hist)

        self._invalidate_cache()

    def move(self, dest: os.PathSpec, overwrite=False):
        dest = pathlib.Path(dest).resolve() / self.name
        os.rename(self._abspath, dest)
        self._abspath = dest

    def rename(self, new_name: str):
        new_path = pathlib.Path(self.abspath.parent / new_name)
        os.rename(self.abspath, new_path)
        self._abspath = new_path


class ObjectNode(FilesystemNode):
    """A node that represents an object"""

    @classmethod
    def from_path(cls, path: os.PathLike, historian: mincepy.Historian = None):
        full_path = pathlib.Path(path).resolve()

        entry = db.fs.find_entry(os.withdb.to_fs_path(full_path), historian=historian)
        if entry is None:
            raise ValueError(f"'{full_path}' is not a valid object path")

        if db.fs.Entry.is_dir(entry):
            raise exceptions.IsADirectoryError(path)

        obj_id = db.fs.Entry.id(entry)
        return ObjectNode(obj_id, entry=entry, historian=historian)

    def __init__(self,
                 obj_id,
                 path=None,
                 record: mincepy.DataRecord = None,
                 meta=None,
                 parent=None,
                 entry: Dict = None,
                 historian: mincepy.Historian = None):
        if record:
            assert obj_id == record.obj_id, "Obj id and record don't match!"

        self._obj_id = obj_id

        super().__init__(entry_id=obj_id,
                         path=path,
                         parent=parent,
                         entry=entry,
                         historian=historian)
        if not db.fs.Entry.is_obj(self._entry):
            raise exceptions.FileNotFoundError(path)
        if not db.fs.Entry.id(self._entry) == obj_id:
            raise ValueError(
                f'Object id ({obj_id}) and entry id ({db.fs.Entry.id(self._entry)}) mismatch')

        self._record = record  # This will be lazily loaded if None

        # Set up the meta
        self._meta = meta

    def __contains__(self, item):
        """Object nodes have no children and so do not contain anything"""
        return False

    def __copy__(self):
        """Make a copy with no parent"""
        return ObjectNode(self._obj_id,
                          path=self._abspath,
                          entry=self._entry,
                          meta=self._meta,
                          record=self._record)

    @property
    def record(self) -> mincepy.DataRecord:
        if self._record is None:
            # Lazily load
            self._record = self._hist.records.get(self.obj_id)

        return self._record

    @property
    def loaded(self):
        try:
            self._hist.get_obj(self._obj_id)
            return True
        except mincepy.NotFound:
            return False

    @property
    def obj(self) -> object:
        return self.record.load()

    @property
    def obj_id(self):
        return self._obj_id

    @property
    def type_id(self):
        return self.record.type_id

    @property
    def type(self):
        try:
            return self._hist.get_obj_type(self.record.type_id)
        except TypeError:
            return self.type_id

    @property
    def ctime(self):
        return db.fs.Entry.ctime(self._entry)

    @property
    def version(self):
        return db.fs.Entry.ver(self._entry)

    @property
    def mtime(self):
        return db.fs.Entry.mtime(self._entry)

    @property
    def creator(self):
        return self.record.get_extra(mincepy.ExtraKeys.CREATED_BY)

    @property
    def meta(self) -> Optional[Dict]:
        self._hist.meta.get(self._obj_id)

    def delete(self):
        self._hist.delete(self._obj_id, imperative=False)

    def move(self, dest: os.PathSpec, overwrite=False):
        dest = pathlib.Path(dest).resolve() / self.name
        db.rename(self.obj_id, dest)
        self._abspath = dest

    def rename(self, new_name: str):
        new_name: pathlib.Path = self.abspath.parent / new_name
        if new_name.is_dir():
            raise exceptions.IsADirectoryError(new_name)

        try:
            db.rename(self._obj_id, new_name)
        except mincepy.DuplicateKeyError:
            raise RuntimeError(f"File with the name '{new_name}' already exists") from None


class ResultsNode(ContainerNode):
    VIEW_PROPERTIES = ('loaded', 'type', 'creator', 'version', 'ctime', 'mtime', 'name', 'str')

    def __init__(self, name='results', parent=None, historian: mincepy.Historian = None):
        super().__init__(name, parent, historian=historian)
        self._view_mode = TABLE_VIEW
        self._show = {'name'}

    def __repr__(self):
        if self._view_mode == TREE_VIEW:
            rep = []
            for child in self.directories:
                for pre, _, node in anytree.RenderTree(child):
                    rep.append(f'{pre}{node.name}')
            for child in self.objects:
                rep.append(str(child))
            return '\n'.join(rep)

        if self._view_mode == TABLE_VIEW:
            rep = []

            if self._deeply_nested():
                # Do the objects first, like linux's 'ls'
                table = self._get_table(self.objects)
                rep.append(tabulate.tabulate(table, tablefmt='plain'))

                for directory in self.directories:
                    dir_repr = []
                    dir_repr.append(f'{directory.name}:')
                    table = self._get_table(directory)
                    dir_repr.append(tabulate.tabulate(table, tablefmt='plain'))
                    rep.append('\n'.join(dir_repr))
            else:
                my_repr = []
                table = self._get_table(self.directories)
                table.extend(self._get_table(self.objects))
                my_repr.append(tabulate.tabulate(table, tablefmt='plain'))
                rep.append('\n'.join(my_repr))

            return '\n\n'.join(rep)

        if self._view_mode == LIST_VIEW:

            repr_list = []
            for child in self:
                repr_list.append('-'.join(self._get_row(child)))

            if sys.stdout.isatty():
                return columnize.columnize(repr_list, displaywidth=utils.get_terminal_width())

            return '\n'.join(repr_list)

        return super().__repr__()

    def __getitem__(self, item):
        result = super().__getitem__(item)
        if isinstance(result, ResultsNode):
            # Transfer the view mode
            result.show(*self._show, mode=self._view_mode)
        return result

    @property
    def showing(self) -> set:
        """Returns the current view properties that are being displayed (if the view mode supports
        them)"""
        return self._show

    @property
    def view_mode(self) -> str:
        return self._view_mode

    @view_mode.setter
    def view_mode(self, new_mode: str):
        assert new_mode in (TREE_VIEW, LIST_VIEW, TABLE_VIEW)
        self._view_mode = new_mode

    def append(self, node: FilesystemNode, display_name: str = None):
        """Append a node to the results"""
        node.parent = self
        display_name = display_name or node.name
        node.display_name = display_name

    def extend(self, other: ContainerNode):
        """Extend this results using incorporating the entries of the other container"""
        for entry in other:
            self.append(entry)

    def show(self, *properties, mode: str = None):
        if mode is not None:
            self._view_mode = mode
        if properties:
            self._show = set(properties)

    def _get_row(self, child) -> Sequence[str]:
        # pylint: disable=too-many-branches
        empty = ''
        row = []

        if 'loaded' in self._show:
            try:
                row.append('*' if child.loaded else '')
            except AttributeError:
                row.append(empty)

        if 'type' in self._show:
            try:
                row.append(fmt.pretty_type_string(child.type))
            except AttributeError:
                row.append('directory')

        if 'creator' in self._show:
            row.append(getattr(child, 'creator', empty))

        if 'version' in self._show:
            row.append(getattr(child, 'version', empty))

        if 'ctime' in self._show:
            try:
                row.append(fmt.pretty_datetime(child.ctime))
            except AttributeError:
                row.append(empty)

        if 'mtime' in self._show:
            try:
                row.append(fmt.pretty_datetime(child.mtime))
            except AttributeError:
                row.append(empty)

        if 'name' in self._show:
            row.append(getattr(child, 'name', empty))

        if 'str' in self._show:
            try:
                row.append(str(getattr(child, 'obj', empty))[:30])
            except (TypeError, mincepy.ObjectDeleted):
                row.append(empty)

        if 'abspath' in self._show:
            row.append(str(getattr(child, 'abspath', empty)))

        if 'relpath' in self._show:
            try:
                row.append(os.path.relpath(child.abspath))
            except AttributeError:
                row.append(empty)

        return row

    def _get_table(self, entry) -> list:
        table = []

        for child in entry:
            table.append(self._get_row(child))

        return table

    def _deeply_nested(self) -> bool:
        """Returns True if we have any nodes that themselves have children"""
        for directory in self.directories:
            if len(directory) > 0:
                return True

        return False


@functools.singledispatch
def to_node(entry, historian: mincepy.Historian = None) -> FilesystemNode:
    """Get the node for a given object.  This can be either:

    1.  An object id -> ObjectNode
    2.  A directory path -> DirectoryNode
    3.  An object path -> ObjectNode
    """
    if db.get_historian().is_obj_id(entry):
        return ObjectNode(entry, historian=historian)

    raise ValueError(f'Unknown entry type: {entry}')


@to_node.register(FilesystemNode)
def _(entry: FilesystemNode, historian: mincepy.Historian = None):
    return entry


@to_node.register(os.PathLike)
def _(path: os.PathLike, historian: mincepy.Historian = None):
    # Make sure we've got a pure path so we don't actually check that database
    path = pathlib.Path(path).resolve()

    fs_entry = db.fs.find_entry(os.withdb.to_fs_path(path), historian=historian)
    if fs_entry is None:
        raise ValueError(f"'{path}' is not a valid object path")

    if db.fs.Entry.is_dir(fs_entry):
        return DirectoryNode(path, entry=fs_entry, historian=historian)

    # Must be object
    return ObjectNode(db.fs.Entry.id(fs_entry), path=path, entry=fs_entry, historian=historian)
