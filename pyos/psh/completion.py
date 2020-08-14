from typing import Iterable, List, Optional, Callable

import pyos
from pyos import glob
from pyos import os as pos
from . import shell

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


def path_complete(app: shell.PyosShell,
                  text: str,
                  _line: str,
                  _begidx: int,
                  _endidx: int,
                  *,
                  path_filter: Optional[Callable[[str], bool]] = None) -> List[str]:
    """Performs completion of local file system paths

    :param app: The pyos base shell
    :param text: the string prefix we are attempting to match (all matches must begin with it)
    :param _line: the current input line with leading whitespace removed
    :param _begidx: the beginning index of the prefix text
    :param _endidx: the ending index of the prefix text
    :param path_filter: optional filter function that determines if a path belongs in the
        results this function takes a path as its argument and returns True if the path should
        be kept in the results
    :return: a list of possible tab completions
    """
    # If the search text is blank, then search in the CWD for *
    if not text:
        search_str = '*'
    else:
        # Purposely don't match any path containing wildcards
        if '*' in text or '?' in text:
            return []

        # Start the search string
        search_str = text + '*'

    # Set this to True for proper quoting of paths with spaces
    app.matches_delimited = True

    # Find all matching path completions
    matches = glob.glob(search_str)

    # Filter out results that don't belong
    if path_filter is not None:
        matches = [c for c in matches if path_filter(c)]

    # Don't append a space or closing quote to directory
    if len(matches) == 1 and pos.path.isdir(matches[0]):
        app.allow_appended_space = False
        app.allow_closing_quote = False

    # Sort the matches before any trailing slashes are added
    matches.sort(key=app.default_sort_key)
    app.matches_sorted = True

    return matches


def file_completer(app: shell.PyosShell, text: str, line: str, begidx: int,
                   endidx: int) -> List[str]:

    def is_file(path: str):
        return not path.endswith(pos.sep)

    return path_complete(app, text, line, begidx, endidx, path_filter=is_file)


def dir_completer(app: shell.PyosShell, text: str, line: str, begidx: int,
                  endidx: int) -> List[str]:

    def is_dir(path: str):
        return path.endswith(pos.sep)

    return path_complete(app, text, line, begidx, endidx, path_filter=is_dir)
