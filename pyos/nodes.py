from abc import ABCMeta
from collections.abc import Sequence
import typing

import anytree
import columnize
import tabulate

import mincepy

from . import constants
from . import fmt
from . import dirs
from . import queries


class BaseNode(Sequence, anytree.NodeMixin, metaclass=ABCMeta):

    def __init__(self, name: str, parent=None):
        super().__init__()
        self._name = name
        self.parent = parent
        self._hist = mincepy.get_historian()

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

    def move(self, where: dirs.PyosPath):
        """Move this object (with any descendents) to the given path"""
        for child in self.children:
            child.move(where)


class PyosNode(BaseNode):
    """Base node for representing an object in the virtual filesystem"""

    def __init__(self, abspath: dirs.PyosPath, parent=None):
        super().__init__(abspath.name, parent)
        self._abspath = abspath

    @property
    def abspath(self) -> dirs.PyosPath:
        return self._abspath


class DirectoryNode(PyosNode):

    def __init__(self, pathname: dirs.PyosPath, parent=None):
        assert pathname.is_dir(), "Must supply a directory path"
        super().__init__(pathname.resolve(), parent)

    def __repr__(self):
        rep = []
        for pre, _, node in anytree.RenderTree(self):
            rep.append("%s%s" % (pre, node.name))
        return "\n".join(rep)

    def __contains__(self, item):
        if isinstance(item, dirs.PyosPath):
            path = item.resolve()
            for child in self.children:
                if path == child.abspath:
                    return True

            return False

        if self._hist.is_obj_id(item):
            for node in self.objects:
                if item == node.obj_id:
                    return True
            return False

        return False

    @property
    def directories(self):
        return filter(lambda node: isinstance(node, DirectoryNode), self.children)

    @property
    def objects(self):
        return filter(lambda node: isinstance(node, ObjectNode), self.children)

    def _invalidate_cache(self):
        self.children = []

    def expand(self, depth=1):
        """Populate the children with what is currently in the database"""
        self.children = []
        metas = self._hist.meta.find(queries.subdirs(str(self._abspath), 0, -1))

        # Get directories and object ids
        dirstring = str(self._abspath)
        child_expand_depth = depth - 1
        directories_added = set()
        for meta in metas:
            directory = meta[constants.DIR_KEY]

            if directory == dirstring:
                # This is an object _in_ this directory
                ObjectNode(meta['obj_id'], meta=meta, parent=self)
            else:
                # This is an object that resides at some subdirectory so we know
                # that there must exist a subdirectory
                if directory not in directories_added:
                    directories_added.add(directory)

                    obj_dir = dirs.PyosPath(directory)
                    path = (self._abspath / obj_dir.parts[len(self._abspath.parts)]).to_dir()

                    dir_node = DirectoryNode(path, parent=self)
                    if abs(child_expand_depth) > 0:
                        dir_node.expand(child_expand_depth)

    def delete(self):
        metas = self._hist.meta.find(queries.subdirs(str(self._abspath), 0, -1))
        objs = self._hist.load(meta['obj_id'] for meta in metas)
        for obj in objs:
            self._hist.delete(obj)
        self._invalidate_cache()

    def move(self, where: dirs.PyosPath):
        assert where.is_dir(), "Can't move a directory to a file"
        where = where.resolve()
        self.expand(1)
        for child in self.children:
            child.move((where / self.name).to_dir())


class ObjectNode(PyosNode):

    @classmethod
    def from_path(cls, path: dirs.PyosPath):
        assert path.is_file()
        path = path.resolve()
        # Let's find the object id
        hist = mincepy.get_historian()
        try:
            obj_id = hist._ensure_obj_id(path.name)
            meta = None
        except mincepy.NotFound:
            results = tuple(
                hist.meta.find(
                    queries.and_(queries.dirmatch(path.parent), {constants.NAME_KEY: path.name})))
            if not results:
                raise ValueError("Object not found: {}".format(path))

            meta = results[0]
            obj_id = meta['obj_id']

        return ObjectNode(obj_id, meta=meta)

    def __init__(self, obj_id, record: mincepy.DataRecord = None, meta=None, parent=None):
        self._hist = mincepy.get_historian()
        self._obj_id = obj_id

        # Set up the record
        if record is None:
            self._record = tuple(self._hist.archive.find(obj_id))[0]  # type: mincepy.DataRecord
        else:
            self._record = record
        assert self._record.obj_id == obj_id

        # Set up the meta
        self._meta = meta
        if self._meta is None:
            try:
                self._meta = self._hist.meta.get(obj_id)
            except mincepy.NotFound:
                pass
        else:
            assert self._meta['obj_id'] == obj_id

        # Set up the abspath
        self._abspath = dirs.get_abspath(obj_id, self._meta)

        super().__init__(self._abspath, parent)

    def __contains__(self, item):
        return item == self.obj_id

    @property
    def loaded(self):
        try:
            self._hist.get_obj(self._obj_id)
            return True
        except mincepy.NotFound:
            return False

    @property
    def abspath(self) -> dirs.PyosPath:
        return self._abspath

    @property
    def obj_id(self):
        return self._obj_id

    @property
    def type(self):
        try:
            return self._hist.get_obj_type(self._record.type_id)
        except TypeError:
            return self._record.type_id

    @property
    def ctime(self):
        return self._record.creation_time

    @property
    def version(self):
        return self._record.version

    @property
    def mtime(self):
        return self._record.snapshot_time

    @property
    def creator(self):
        return self._record.get_extra(mincepy.ExtraKeys.CREATED_BY)

    @property
    def meta(self) -> dict:
        return self._meta

    def delete(self):
        self._hist.delete(self._hist.load_one(self._obj_id))

    def move(self, where: dirs.PyosPath):
        meta_update = dirs.path_to_meta_dict(where)
        self._hist.meta.update(self._obj_id, meta_update)


LIST_VIEW = 'list'
TREE_VIEW = 'tree'
TABLE_VIEW = 'table'


class ResultsNode(BaseNode):
    VIEW_PROPERTIES = ('loaded', 'type', 'creator', 'version', 'ctime', 'mtime', 'name', 'str')

    def __init__(self, name='results', parent=None):
        super().__init__(name, parent)
        self._view_mode = TABLE_VIEW
        self._show = {'name'}

    def __contains__(self, item):
        if isinstance(item, dirs.PyosPath):
            path = item.resolve()
            for child in self.children:
                if path == child.abspath:
                    return True

            return False

        if self._hist.is_obj_id(item):
            for node in self.objects:
                if item == node.obj_id:
                    return True
            return False

        return False

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

            return columnize.columnize(repr_list, displaywidth=100)

        return super().__repr__()

    @property
    def directories(self):
        return filter(lambda node: isinstance(node, DirectoryNode), self.children)

    @property
    def objects(self):
        return filter(lambda node: isinstance(node, ObjectNode), self.children)

    def append(self, node: PyosNode, display_name: str = None):
        node.parent = self
        display_name = display_name or node.name
        node.display_name = display_name

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
            row.append(str(child))

        if 'abspath' in self._show:
            row.append(str(getattr(child, 'abspath', empty)))

        return row

    def _get_table(self, entry):
        table = []

        for child in entry:
            table.append(self._get_row(child))

        return table

    def _deeply_nested(self) -> bool:
        for directory in self.directories:
            if len(directory) > 0:
                return True

        return False


def to_node(entry) -> PyosNode:
    """Get the node for a given object.  This can be either:
    1. An object id -> ObjectNode
    2. A directory path -> DirectoryNode
    3. An object path -> ObjectNode
    """
    hist = mincepy.get_historian()
    if hist.is_obj_id(entry):
        return ObjectNode(entry)
    if isinstance(entry, dirs.PyosPath):
        if entry.is_dir():
            return DirectoryNode(entry)

        return ObjectNode.from_path(entry)

    raise ValueError("Unknown entry type: {}".format(entry))
