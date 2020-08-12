import abc
from collections.abc import Sequence, Set
import copy
import functools
import typing

import anytree
import columnize
import tabulate

import mincepy

from pyos import config
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


class BaseNode(Sequence, anytree.NodeMixin, results.BaseResults, metaclass=abc.ABCMeta):

    def __init__(self, name: str, parent=None):
        super().__init__()
        self._name = name
        self.parent = parent
        self._hist = db.get_historian()

    def __getitem__(self, item):
        return self.children.__getitem__(item)

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

    def __init__(self, path: os.PathSpec, parent: BaseNode = None):
        """
        :param path: the path this node represents
        :param parent: parent node
        """
        path = pathlib.Path(path).resolve()
        super().__init__(path.name, parent)
        self._abspath = path

    @property
    def abspath(self) -> 'pathlib.Path':
        return self._abspath

    @abc.abstractmethod
    def rename(self, new_name: str):
        """Rename this filesystem node"""


class ContainerNode(BaseNode):
    """A node that contains children that can be either directory nodes or object nodes"""

    def __contains__(self, item):
        # pylint: disable=too-many-nested-blocks, too-many-branches, too-many-return-statements
        if isinstance(item, pathlib.PurePath):
            path = pathlib.PurePath(item)
            if path.is_absolute():
                if path.is_dir_path():
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
                    subpath = pathlib.PurePath("".join(parts[1:]))

                    # Check subdirs
                    for node in self.directories:
                        if node.abspath.name == parts[0] and subpath in node:
                            return True
                else:
                    if path.is_dir_path():
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
        items = super(ContainerNode, self).__getitem__(item)
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

    def __init__(self, path: os.PathSpec, parent: BaseNode = None):
        path = pathlib.PurePath(path)
        assert path.is_dir_path(), "Must supply a directory path"
        super().__init__(path.resolve(), parent)

    def __repr__(self):
        rep = []
        for pre, _, node in anytree.RenderTree(self):
            rep.append("%s%s" % (pre, node.name))
        return "\n".join(rep)

    def __copy__(self):
        """Create a copy with no parent"""
        dir_node = DirectoryNode(self.abspath)
        dir_node.children = [copy.copy(child) for child in self.children]
        return dir_node

    def _invalidate_cache(self):
        self.children = []

    def expand(self, depth=1, populate_objects=False):
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

        path_str = str(self._abspath)

        # OBJECTS
        # Query for objects in this directory
        obj_kwargs = []
        for obj_id, meta in self._hist.meta.find({config.DIR_KEY: path_str}):
            # This is an object in _this_ directory and not further down the hierarchy
            obj_kwargs.append(dict(obj_id=obj_id, meta=meta, parent=self))

        # DIRECTORIES

        # Search for objects in directories below this one (depth 1) to any depth (-1) as
        # there may be just folders (no objects) between _abspath and the object in some deeply
        # nested directory
        directories = self._hist.meta.distinct(config.DIR_KEY,
                                               {config.DIR_KEY: {
                                                   '$regex': '^' + path_str
                                               }})

        len_path_str = len(path_str)

        child_expand_depth = depth - 1
        directories_added = set()  # type: Set[str]

        for dirstring in directories:
            if dirstring == path_str:
                # Skip over this directory
                continue

            # This is an object that resides at some subdirectory so we know
            # that there must exist a subdirectory
            dirname = dirstring[len_path_str:].split(os.sep)[0]

            if dirname not in directories_added:
                directories_added.add(dirname)
                # Get the subdirectory relative to us
                path = (self._abspath / dirname).to_dir()

                dir_node = DirectoryNode(path, parent=self)
                if abs(child_expand_depth) > 0:
                    dir_node.expand(child_expand_depth)

        if populate_objects:
            # Gather all the object ids
            obj_ids = [kwargs['obj_id'] for kwargs in obj_kwargs]
            records = {record.obj_id: record for record in self._hist.archive.find(obj_id=obj_ids)}
            for kwargs in obj_kwargs:
                kwargs['record'] = records[kwargs['obj_id']]

        for kwargs in obj_kwargs:
            ObjectNode(**kwargs)

    def delete(self):
        with self._hist.transaction():
            for obj_id, _meta in self._hist.meta.find(db.queries.subdirs(str(self._abspath), 0,
                                                                         -1)):
                self._hist.delete(obj_id)
        self._invalidate_cache()

    def move(self, dest: os.PathSpec, overwrite=False):
        dest = pathlib.Path(dest).to_dir().resolve() / self.name
        os.rename(self._abspath, dest)
        self._abspath = dest

    def rename(self, new_name: str):
        new_path = pathlib.Path(self.abspath.parent / new_name).to_dir()
        os.rename(self.abspath, new_path)
        self._abspath = new_path


class ObjectNode(FilesystemNode):
    """A node that represents an object"""

    @classmethod
    def from_path(cls, path: os.PathLike):
        path = pathlib.PurePath(path)
        if path.is_dir_path():
            raise exceptions.IsADirectoryError(path)

        path = path.resolve()
        meta = None
        # Let's find the object id
        obj_id = db.to_obj_id(path.name)
        if obj_id is None:
            # Ok, have to do a lookup
            res = tuple(db.find_meta(db.path_to_meta_dict(path)))
            if not res:
                raise ValueError("'{}' is not a valid object path".format(path))

            obj_id, meta = res[0]

        return ObjectNode(obj_id, meta=meta)

    def __init__(self, obj_id, record: mincepy.DataRecord = None, meta=None, parent=None):
        if record:
            assert obj_id == record.obj_id, "Obj id and record don't match!"

        self._hist = db.get_historian()
        self._obj_id = obj_id
        self._record = record  # This will be lazily loaded if None

        # Set up the meta
        self._meta = meta
        if self._meta is None:
            self._meta = self._hist.meta.get(obj_id)
            if self._meta is None:
                # Still don't have metadata! Double check this object actually exists
                try:
                    record = next(self._hist.archive.find(obj_id=obj_id,
                                                          deleted=True))  # type: mincepy.DataRecord
                except StopIteration:
                    raise ValueError("Object with id '{}' not found".format(obj_id))
                else:
                    if record.is_deleted_record():
                        raise ValueError("Object with id '{}' has been deleted".format(obj_id))
                    self._record = record
                    self._meta = {}

        # Set up the abspath
        abspath = db.get_abspath(obj_id, self._meta)
        super().__init__(abspath, parent)

    def __contains__(self, item):
        """Object nodes have no children and so do not contain anything"""
        return False

    def __copy__(self):
        """Make a copy with no parent"""
        return ObjectNode(self._obj_id, meta=self._meta, record=self._record)

    @property
    def record(self) -> mincepy.DataRecord:
        if self._record is None:
            # Lazily load
            self._record = tuple(self._hist.archive.find(
                self._obj_id))[0]  # type: mincepy.DataRecord

        return self._record

    @property
    def loaded(self):
        try:
            self._hist.get_obj(self._obj_id)
            return True
        except mincepy.NotFound:
            return False

    @property
    def obj(self) -> typing.Any:
        return self._hist.load(self._obj_id)

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
        return self.record.creation_time

    @property
    def version(self):
        return self.record.version

    @property
    def mtime(self):
        return self.record.snapshot_time

    @property
    def creator(self):
        return self.record.get_extra(mincepy.ExtraKeys.CREATED_BY)

    @property
    def meta(self) -> dict:
        return self._meta

    def delete(self):
        self._hist.delete(self._obj_id)

    def move(self, dest: os.PathSpec, overwrite=False):
        dest = pathlib.Path(dest).to_dir().resolve() / self.name
        db.rename(self.obj_id, dest)
        self._abspath = dest

    def rename(self, new_name: str):
        new_name = self.abspath.parent / new_name
        if new_name.is_dir():
            raise exceptions.IsADirectoryError(new_name)

        try:
            db.rename(self._obj_id, new_name)
        except mincepy.DuplicateKeyError:
            raise RuntimeError("File with the name '{}' already exists".format(new_name))


class ResultsNode(ContainerNode):
    VIEW_PROPERTIES = ('loaded', 'type', 'creator', 'version', 'ctime', 'mtime', 'name', 'str')

    def __init__(self, name='results', parent=None):
        super().__init__(name, parent)
        self._view_mode = TABLE_VIEW
        self._show = {'name'}

    def __repr__(self):
        if self._view_mode == TREE_VIEW:
            rep = []
            for child in self.directories:
                for pre, _, node in anytree.RenderTree(child):
                    rep.append("%s%s" % (pre, node.name))
            for child in self.objects:
                rep.append(str(child))
            return "\n".join(rep)

        if self._view_mode == TABLE_VIEW:
            rep = []

            if self._deeply_nested():
                # Do the objects first, like linux's 'ls'
                table = self._get_table(self.objects)
                rep.append(tabulate.tabulate(table, tablefmt='plain'))

                for directory in self.directories:
                    dir_repr = []
                    dir_repr.append("{}:".format(directory.name))
                    table = self._get_table(directory)
                    dir_repr.append(tabulate.tabulate(table, tablefmt='plain'))
                    rep.append("\n".join(dir_repr))
            else:
                my_repr = []
                table = self._get_table(self.directories)
                table.extend(self._get_table(self.objects))
                my_repr.append(tabulate.tabulate(table, tablefmt='plain'))
                rep.append("\n".join(my_repr))

            return "\n\n".join(rep)

        if self._view_mode == LIST_VIEW:

            repr_list = []
            for child in self:
                repr_list.append("-".join(self._get_row(child)))

            return columnize.columnize(repr_list, displaywidth=utils.get_terminal_width())

        return super().__repr__()

    def __getitem__(self, item):
        result = super(ResultsNode, self).__getitem__(item)
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

    def _get_row(self, child) -> typing.Sequence[str]:
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
def to_node(entry) -> FilesystemNode:
    """Get the node for a given object.  This can be either:

    1.  An object id -> ObjectNode
    2.  A directory path -> DirectoryNode
    3.  An object path -> ObjectNode
    """
    if db.get_historian().is_obj_id(entry):
        return ObjectNode(entry)

    raise ValueError("Unknown entry type: {}".format(entry))


@to_node.register(FilesystemNode)
def _(entry: FilesystemNode):
    return entry


@to_node.register(os.PathLike)
def _(entry: os.PathLike):
    # Make sure we've got a pure path so we don't actually check that database
    entry = pathlib.PurePath(entry)

    if entry.is_dir_path():
        return DirectoryNode(entry)

    return ObjectNode.from_path(entry)
