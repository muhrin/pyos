from abc import ABCMeta
from collections.abc import Sequence

import anytree
import mincepy

from . import constants
from . import dirs
from . import queries


class BaseNode(Sequence, anytree.NodeMixin, metaclass=ABCMeta):

    def __init__(self, name: str, parent=None):
        super().__init__()
        self._name = name
        self.parent = parent

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
        self._hist = mincepy.get_historian()

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
        for child in self.children:
            if item in child:
                return True
        return False

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
                    if child_expand_depth > 0:
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
            meta = tuple(
                hist.meta.find(
                    queries.and_(queries.dirmatch(path.parent),
                                 {constants.NAME_KEY: path.name})))[0]
            obj_id = meta['obj_id']

        return ObjectNode(obj_id, meta=meta)

    def __init__(self, obj_id, record=None, meta=None, parent=None):
        self._hist = mincepy.get_historian()
        self._obj_id = obj_id

        # Set up the record
        if record is None:
            self._record = tuple(self._hist.archive.find(obj_id))[0]
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
    def abspath(self) -> dirs.PyosPath:
        return self._abspath

    @property
    def obj_id(self):
        return self._obj_id

    @property
    def meta(self) -> dict:
        return self._meta

    def delete(self):
        self._hist.delete(self._hist.load_one(self._obj_id))

    def move(self, where: dirs.PyosPath):
        meta_update = dirs.path_to_meta_dict(where)
        self._hist.meta.update(self._obj_id, meta_update)


class ResultsNode(BaseNode):

    def __init__(self, parent=None):
        super().__init__('results', parent)

    def __contains__(self, item) -> bool:
        for child in self.children:
            if item in child:
                return True

        return False

    def __repr__(self):
        rep = []
        for pre, _, node in anytree.RenderTree(self):
            rep.append("%s%s" % (pre, node.name))
        return "\n".join(rep)

    def append(self, node: PyosNode, display_name: str = None):
        node.parent = self
        display_name = display_name or node.name
        node.display_name = display_name


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

    raise TypeError("Unknown entry type '{}'".format(type(entry)))
