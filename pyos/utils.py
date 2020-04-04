import copy
from typing import Sequence, Iterable
import collections.abc

import mincepy

from . import constants
from . import dirs
from . import nodes

__all__ = ('CachingResults',)


def parse_args(*args) -> Sequence:
    parsed = []
    hist = mincepy.get_historian()
    for arg in args:
        if arg is None:
            parsed.append(None)
        elif isinstance(arg, nodes.ObjectNode):
            parsed.append(copy.copy(arg))
        elif isinstance(arg, nodes.DirectoryNode):
            parsed.append(copy.copy(arg))
        elif isinstance(arg, nodes.ResultsNode):
            parsed.extend(parse_args(*arg.children))
        elif isinstance(arg, dirs.PyosPath):
            parsed.append(arg)
        elif hist.is_obj_id(arg):
            parsed.append(arg)
        else:
            try:
                # Maybe it's an object id
                parsed.append(hist._ensure_obj_id(arg))
                continue
            except mincepy.NotFound:
                pass

            # Maybe it's a live object
            obj_id = hist.get_obj_id(arg)
            if obj_id is not None:
                parsed.append(obj_id)
            elif isinstance(arg, str):
                # Assume it's a path
                parsed.append(dirs.PyosPath(arg))
            else:
                raise TypeError("Unknown type '{}'".format(arg))

    return parsed


def new_meta(orig: dict, new: dict) -> dict:
    merged = new.copy()
    if not orig:
        return merged

    for name in constants.KEYS:
        if name in orig:
            if name.startswith('_'):
                # Always take internal, i.e. underscored, keys
                merged[name] = orig[name]
            else:
                merged.setdefault(name, orig[name])

    return merged


class CachingResults(collections.abc.Sequence):
    """A helper that takes an iterable and wraps it caching the results as a sequence."""

    def __init__(self, iterable: Iterable):
        super().__init__()
        self._iterable = iterable
        self._cache = []

    def __getitem__(self, item):
        self._ensure_cache(item)
        return self._cache[item]

    def __iter__(self):
        return self._iter_generator()

    def __len__(self):
        self._ensure_cache()
        return len(self._cache)

    def __repr__(self):
        return "\n".join([str(item) for item in self])

    def _iter_generator(self, at_end=False):
        idx = 0 if not at_end else len(self._cache)
        while True:
            if idx >= len(self._cache):
                # Ok, try the iterable
                if self._iterable is None:
                    return

                try:
                    self._cache.append(next(self._iterable))
                except StopIteration:
                    self._iterable = None
                    return

            yield self._cache[idx]
            idx += 1

    def _ensure_cache(self, max_index=-1):
        """Fill up the cache up to the max index.  If -1 then fill up entirely"""
        if self._iterable is None or (0 <= max_index < len(self._cache)):
            return

        idx = len(self._cache)
        self_iter = self._iter_generator(at_end=True)
        while True:
            try:
                next(self_iter)
                idx += 1
                if idx == max_index:
                    return
            except StopIteration:
                return
