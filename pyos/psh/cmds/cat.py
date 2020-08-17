import argparse
import logging
import re
import sys

import cmd2

import pyos
from pyos import db
from pyos import psh
from pyos.psh import completion

_LOGGER = logging.getLogger(__name__)


@pyos.psh_lib.command()
def cat(*obj_or_ids, representer=None):
    """Convert the contents of objects into strings.
    A representer can optionally be passed in which should take the passed object and convert it to
    a string.
    """
    if not obj_or_ids:
        return None

    hist = db.get_historian()
    to_cat = []

    for entry in obj_or_ids:
        if isinstance(entry,
                      (str, pyos.pathlib.Path, pyos.fs.BaseNode, hist.archive.get_id_type())):
            to_cat.extend(psh.ls(-psh.d, entry))
        else:
            to_cat.append(entry)

    representer = representer or pyos.psh_lib.get_default()

    def iterator():
        for node in to_cat:
            try:
                if isinstance(node, pyos.fs.DirectoryNode):
                    yield "cat: {}: Is a directory".format(node.abspath.name)
                elif isinstance(node, pyos.fs.ObjectNode):
                    yield representer(node.obj)
                else:
                    yield representer(node)
            except Exception as exc:  # pylint: disable=broad-except
                yield representer(exc)

    results = pyos.psh_lib.CachingResults(iterator(), representer=str)

    if len(to_cat) == 1:
        return pyos.psh_lib.ResultsString(results[0])

    return results


class FstringRepresenter:
    REGEXP = re.compile(r'{(\S*)}')

    def __init__(self, fstring):
        # Create the adapted f-string with 'obj' representing the passed object
        self._fstring = self.REGEXP.subn('{obj\\1}', fstring)[0]

    def __call__(self, obj) -> str:
        return self._fstring.format(obj=obj)


class Cat(cmd2.CommandSet):
    ls_parser = argparse.ArgumentParser()
    ls_parser.add_argument('-f',
                           dest='fstring',
                           type=str,
                           help="optional f-string for printing attributes e.g. -f {colour} prints "
                           "obj.colour for each object")
    ls_parser.add_argument('path', nargs='*', type=str, completer_method=completion.file_completer)

    @cmd2.with_argparser(ls_parser)
    def do_cat(self, args):  # pylint: disable=no-self-use
        if not args.path:
            # Read from standard in
            _LOGGER.debug("cat: getting input from stdin")
            try:
                args.path = [line.rstrip() for line in sys.stdin.readlines()]
            except Exception:
                _LOGGER.exception("Exception trying to readlines")
                raise
            _LOGGER.debug("cat: got input' %s' from stdin", args.path)

        representer = None
        if args.fstring:
            representer = FstringRepresenter(args.fstring)

        results = cat(*args.path, representer=representer)

        if isinstance(results, pyos.psh_lib.ResultsString):
            print(results)
        else:
            for entry in results:
                print(entry)
