"""Module that contains classes used to provide results to the user"""
import collections.abc
from typing import Callable, Iterator

import pyos.results
from pyos.psh_lib import representers

__all__ = 'CachingResults', 'ResultsDict', 'ResultsString'


class CachingResults(collections.abc.Sequence, pyos.results.BaseResults):
    """A helper that takes an iterator and wraps it caching the results as a sequence."""

    def __init__(self, iterator: Iterator, representer: Callable = None):
        """
        Create a caching results sequence.  If no representer is supplied the default will be used.

        :param iterator: the iterable to cache results of
        :param representer: the representer to use, if None the current default will be used.
        """
        super().__init__()
        self._iterator = iterator
        self._representer = representer or representers.get_default()
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
        return "\n".join([self._representer(item) for item in self])

    def _iter_generator(self, at_end=False):
        idx = 0 if not at_end else len(self._cache)
        while True:
            if idx >= len(self._cache):
                # Ok, try the iterable
                if self._iterator is None:
                    return

                try:
                    self._cache.append(next(self._iterator))
                except StopIteration:
                    self._iterator = None
                    return

            yield self._cache[idx]
            idx += 1

    def _ensure_cache(self, max_index=-1):
        """Fill up the cache up to the max index.  If -1 then fill up entirely"""
        if self._iterator is None or (0 <= max_index < len(self._cache)):
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


class ResultsDict(collections.abc.Mapping, pyos.results.BaseResults):
    """A custom dictionary representing results from a command"""

    def __init__(self, results: dict, representer=None):
        self._results = results
        self._representer = representer or representers.get_default()

    def __getitem__(self, item):
        return self._results.__getitem__(item)

    def __iter__(self):
        return self._results.__iter__()

    def __len__(self):
        return self._results.__len__()

    def __repr__(self):
        return self._representer(self)


class ResultsString(collections.UserString, pyos.results.BaseResults):
    """A string that overwrites the __repr__ method"""

    def __init__(self, result: str, representer=None):
        super().__init__(result)
        self._representer = representer or representers.get_default()

    def __repr__(self):
        return self._representer(self.data)
