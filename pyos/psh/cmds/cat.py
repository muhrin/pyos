import argparse

import cmd2

import pyos
from pyos import db
from pyos import psh
from pyos.psh import base


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


class Cat(cmd2.CommandSet):
    ls_parser = argparse.ArgumentParser()
    ls_parser.add_argument('path', nargs='*', type=str, completer_method=base.file_completer)

    @cmd2.with_argparser(ls_parser)
    def do_cat(self, app: cmd2.Cmd, args):  # pylint: disable=no-self-use
        command = cat

        app.poutput(command(*args.path))
