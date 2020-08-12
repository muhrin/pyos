import os
from typing import List, Callable, Optional

import click
import mincepy
import cmd2.plugin

import pyos
from pyos import db
from pyos import os
from pyos import glob
from pyos import version


def mod() -> str:
    """Get the message of the day string"""
    message = [
        version.BANNER,
        " Powered by mincePy (v{})".format(mincepy.__version__),  # pylint: disable=no-member
        ' https://pyos.readthedocs.io/en/latest/',
        ''
    ]

    return "\n".join(message)


class BaseShell(cmd2.Cmd):
    """The pyOS shell"""

    def __init__(self):
        hist_path = os.path.join(click.get_app_dir('pyos'), 'psh_history')
        super().__init__(use_ipython=True, persistent_history_file=hist_path)

        try:
            pyos.lib.init()
        except (mincepy.ConnectionError, ValueError):
            pass

        self.intro = mod()
        self._update_prompt()
        self.register_cmdfinalization_hook(self.command_finalise)

    def command_finalise(
            self, data: cmd2.plugin.CommandFinalizationData) -> cmd2.plugin.CommandFinalizationData:
        self._update_prompt()
        return data

    def _update_prompt(self):
        try:
            historian = db.get_historian()
        except RuntimeError:
            # Happens when there is a global historian but pyos.db.init() hasn't been called
            historian = None

        if historian is None:
            self.prompt = '[not connected]$ '
        else:
            self.prompt = "{}$ ".format(pyos.os.getcwd())


def path_complete(_cmd_set: cmd2.CommandSet,
                  app: BaseShell,
                  text: str,
                  _line: str,
                  _begidx: int,
                  _endidx: int,
                  *,
                  path_filter: Optional[Callable[[str], bool]] = None) -> List[str]:
    """Performs completion of local file system paths

    :param app: The pyos base shell
    :param _cmd_set: the command set
    :param text: the string prefix we are attempting to match (all matches must begin with it)
    :param line: the current input line with leading whitespace removed
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
    if len(matches) == 1 and os.path.isdir(matches[0]):
        app.allow_appended_space = False
        app.allow_closing_quote = False

    # Sort the matches before any trailing slashes are added
    matches.sort(key=app.default_sort_key)
    app.matches_sorted = True

    return matches


def file_completer(cmd_set: cmd2.CommandSet, app: BaseShell, text: str, line: str, begidx: int,
                   endidx: int) -> List[str]:

    def is_file(path: str):
        return not path.endswith(os.sep)

    return path_complete(cmd_set, app, text, line, begidx, endidx, path_filter=is_file)


def dir_completer(cmd_set: cmd2.CommandSet, app: BaseShell, text: str, line: str, begidx: int,
                  endidx: int) -> List[str]:

    def is_dir(path: str):
        return path.endswith(os.sep)

    return path_complete(cmd_set, app, text, line, begidx, endidx, path_filter=is_dir)
