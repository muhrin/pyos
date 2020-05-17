from typing import Iterable

import pyos

__all__ = ('PathCompletion',)


class PathCompletion(pyos.os.PathLike):
    """This class enables tab-completion for paths.  Passed a path, this class will list all the
    files and directories below it when __dir__ is called (i.e. tab in, e.g., ipython)."""

    def __init__(self, path='.'):
        self._path = pyos.pathlib.Path(path)

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self._path)

    def __fspath__(self):
        return str(self._path)

    def __dir__(self) -> Iterable[str]:
        try:
            for path in self._path.to_dir().iterdir():
                name = path.name
                if name.endswith('/'):
                    name = name[:-1]

                # Skip strings that aren't python identifiers
                if name.isidentifier():
                    yield name

        except (pyos.FileNotFoundError, pyos.NotADirectoryError):
            pass

    def _ipython_key_completions_(self):
        """This allows getitem style (["<tab>) style completion"""
        try:
            for path in self._path.to_dir().iterdir():
                yield path.name

        except (pyos.FileNotFoundError, pyos.NotADirectoryError):
            pass

    def __getattr__(self, item: str) -> 'PathCompletion':
        """Attribute access for paths"""
        # This creates a file (because forward slash isn't a valid python variable name character),
        # but it may be a directory..

        path = self._path / item
        # ..check:
        if not path.exists():
            path = path.to_dir()
            if not path.exists():
                try:
                    return super().__getattr__(item)
                except AttributeError:
                    raise AttributeError("Path does not exist: '{}'".format(item))

        return PathCompletion(path)

    def __getitem__(self, item):
        """Square bracket notation.  Allows arbitrary strings which is needed if the path name isn't
        a valid python variable"""
        path = self._path / item
        if path.exists():
            return PathCompletion(path)

        path = path.to_dir()
        if path.exists():
            return PathCompletion(path)

        raise FileNotFoundError("Path does not exist: '{}'".format(item))
