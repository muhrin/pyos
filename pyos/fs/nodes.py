import abc
from collections.abc import Sequence
import copy
import functools
import typing

import anytree
import columnize
import tabulate

import mincepy
import mincepy.qops

import pyos
import pyos.results

__all__ = ('BaseNode', 'DirectoryNode', 'ObjectNode', 'ResultsNode', 'to_node', 'TABLE_VIEW',
           'LIST_VIEW', 'TREE_VIEW', 'find')

LIST_VIEW = 'list'
TREE_VIEW = 'tree'
TABLE_VIEW = 'table'


class BaseNode(Sequence, anytree.NodeMixin, pyos.results.BaseResults, metaclass=abc.ABCMeta):

    def __init__(self, name: str, parent=None):
        super().__init__()
        self._name = name
        self.parent = parent
        self._hist = pyos.db.get_historian()

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

    def move(self, where, overwrite=False):
        """Move this object (with any descendents) to the given path

        :type where: pyos.os.PathLike
        :param overwrite: overwrite if exists
        """
        for child in self.children:
            child.move(where, overwrite)


class FilesystemNode(BaseNode):
    """Base node for representing an object in the virtual filesystem"""

    def __init__(self, path: pyos.os.PathSpec, parent: BaseNode = None):
        """
        :param path: the path this not represents
        :param parent: parent node
        """
        path = pyos.Path(path).resolve()
        super().__init__(path.name, parent)
        self._abspath = path

    @property
    def abspath(self) -> pyos.pathlib.Path:
        return self._abspath

    @abc.abstractmethod
    def rename(self, new_name: str):
        """Rename this filesystem node"""


class ContainerNode(BaseNode):
    """A node that contains children that can be either directory nodes or object nodes"""

    def __contains__(self, item):
        if isinstance(item, pyos.PurePath):
            path = pyos.PurePath(item)
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
                    subpath = pyos.PurePath("".join(parts[1:]))

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
            results = ResultsNode()
            for entry in items:
                results.append(copy.copy(entry))
            return results

        return items

    @property
    def directories(self):
        return filter(lambda node: isinstance(node, DirectoryNode), self.children)

    @property
    def objects(self):
        return filter(lambda node: isinstance(node, ObjectNode), self.children)


class DirectoryNode(ContainerNode, FilesystemNode):

    def __init__(self, path: pyos.os.PathSpec, parent: BaseNode = None):
        path = pyos.pathlib.PurePath(path)
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

        metas = self._hist.meta.find(pyos.db.queries.subdirs(str(self._abspath), 0, -1))

        # Get directories and object ids
        dirstring = str(self._abspath)
        child_expand_depth = depth - 1
        directories_added = set()

        obj_kwargs = []
        for obj_id, meta in metas:
            directory = meta[pyos.config.DIR_KEY]

            if directory == dirstring:
                # This is an object in _this_ directory and not further down the hierarchy
                obj_kwargs.append(dict(obj_id=obj_id, meta=meta, parent=self))
            else:
                # This is an object that resides at some subdirectory so we know
                # that there must exist a subdirectory

                # Get the subdirectory relative to us
                obj_dir = pyos.pathlib.PurePath(directory)
                path = (self._abspath / obj_dir.parts[len(self._abspath.parts)]).to_dir()
                if path not in directories_added:
                    directories_added.add(path)

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
            for obj_id, _meta in self._hist.meta.find(
                    pyos.db.queries.subdirs(str(self._abspath), 0, -1)):
                self._hist.delete(obj_id)
        self._invalidate_cache()

    def move(self, where: pyos.os.PathSpec, overwrite=False):
        where = pyos.pathlib.Path(where).to_dir()

        # The new path is the dest directory plus our current name
        newpath = where.resolve() / self.name

        if newpath.is_dir():
            raise RuntimeError("Directory '{}' already exists".format(newpath))

        with self._hist.transaction():
            self.expand(1)
            for child in self.children:
                child.move((newpath / self.name).to_dir())

        self._abspath = newpath

    def rename(self, new_name: str):
        newpath = pyos.Path(self.abspath.parent / new_name).to_dir()

        if newpath.is_dir():
            raise RuntimeError("Folder with the name '{}' already exists".format(new_name))

        with self._hist.transaction():
            self.expand(1)
            for child in self.children:
                child.move(newpath)

        self._abspath = newpath


class ObjectNode(FilesystemNode):
    """A node that represents an object"""

    @classmethod
    def from_path(cls, path: pyos.os.PathLike):
        path = pyos.pathlib.PurePath(path)
        if path.is_dir_path():
            raise pyos.IsADirectoryError(path)

        path = path.resolve()
        meta = None
        # Let's find the object id
        obj_id = pyos.db.to_obj_id(path.name)
        if obj_id is None:
            # Ok, have to do a lookup
            results = tuple(pyos.db.find_meta(pyos.db.path_to_meta_dict(path)))
            if not results:
                raise ValueError("'{}' is not a valid object path".format(path))

            obj_id, meta = results[0]

        return ObjectNode(obj_id, meta=meta)

    def __init__(self, obj_id, record: mincepy.DataRecord = None, meta=None, parent=None):
        if record:
            assert obj_id == record.obj_id, "Obj id and record don't match!"

        self._hist = pyos.db.get_historian()
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
        abspath = pyos.db.get_abspath(obj_id, self._meta)
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

    def move(self, where: pyos.pathlib.PurePath, overwrite=False):
        where = pyos.pathlib.PurePath(where)
        meta_update = pyos.db.path_to_meta_dict(where)
        try:
            self._hist.meta.update(self._obj_id, meta_update)
        except mincepy.DuplicateKeyError as exc:
            if overwrite:
                # Delete the current one
                # Copy over the path specification
                path_spec = {
                    key: meta_update[key] for key in (pyos.config.NAME_KEY, pyos.config.NAME_KEY)
                }

                try:
                    results = tuple(self._hist.meta.find(path_spec))
                    assert len(results) <= 1, \
                        "Shouldn't be possible to have more than one object with the same path, " \
                        "check the indexes"

                    to_delete = results[0].obj_id
                except IndexError:
                    # Give up
                    raise exc
                else:
                    self._hist.delete(to_delete)

                # One more time...
                self._hist.meta.update(self._obj_id, meta_update)

    def rename(self, new_name: str):
        try:
            self._hist.meta.update(self._obj_id, {pyos.config.NAME_KEY: new_name})
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

            return columnize.columnize(repr_list, displaywidth=pyos.psh_lib.get_terminal_width())

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
                row.append(pyos.fmt.pretty_type_string(child.type))
            except AttributeError:
                row.append('directory')

        if 'creator' in self._show:
            row.append(getattr(child, 'creator', empty))

        if 'version' in self._show:
            row.append(getattr(child, 'version', empty))

        if 'ctime' in self._show:
            try:
                row.append(pyos.fmt.pretty_datetime(child.ctime))
            except AttributeError:
                row.append(empty)

        if 'mtime' in self._show:
            try:
                row.append(pyos.fmt.pretty_datetime(child.mtime))
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
                row.append(pyos.os.path.relpath(child.abspath))
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
    if pyos.db.get_historian().is_obj_id(entry):
        return ObjectNode(entry)

    raise ValueError("Unknown entry type: {}".format(entry))


@to_node.register(FilesystemNode)
def _(entry: FilesystemNode):
    return entry


@to_node.register(pyos.os.PathLike)
def _(entry: pyos.os.PathLike):
    # Make sure we've got a pure path so we don't actually check that database
    entry = pyos.pathlib.PurePath(entry)

    if entry.is_dir_path():
        return DirectoryNode(entry)

    return ObjectNode.from_path(entry)


# pylint: disable=redefined-builtin
def find(*starting_point,
         meta: dict = None,
         state: dict = None,
         type=None,
         mindepth=0,
         maxdepth=-1):
    """
    Find objects matching the given criteria

    :param starting_point: the starting points for the search, if not supplied defaults to '/'
    :param meta: filter criteria for the metadata
    :param state: filter criteria for the object's saved state
    :param type: restrict the search to this type (can be a tuple of types)
    :param mindepth: the minimum depth from the starting point(s) to search in
    :param maxdepth: the maximum depth from the starting point(s) to search in
    :return: results node
    :rtype: pyos.os.ResultsNode
    """
    if not starting_point:
        starting_point = (pyos.os.getcwd(),)
    meta = (meta or {}).copy()
    state = (state or {}).copy()

    # Converting starting points to abspaths
    spoints = [str(pyos.PurePath(path).to_dir().resolve()) for path in starting_point]

    # Add the directory search criteria to the meta search
    subdirs_query = (pyos.db.queries.subdirs(point, mindepth, maxdepth) for point in spoints)
    meta.update(pyos.db.queries.or_(*subdirs_query))

    hist = pyos.db.get_historian()

    # Find the metadata
    metas = dict(hist.meta.find(meta))
    records = {}
    if metas and (type is not None or state is not None):
        # Further restrict the match
        obj_id_filter = mincepy.qops.in_(*metas.keys())
        for record in hist.find_records(obj_id=obj_id_filter, obj_type=type, state=state):
            records[record.obj_id] = record

    results = pyos.fs.ResultsNode()
    results.show('relpath')

    for obj_id, record in records.items():
        node = pyos.fs.ObjectNode(obj_id, record=record, meta=metas[obj_id])
        results.append(node)

    return results
