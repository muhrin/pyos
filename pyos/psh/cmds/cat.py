import mincepy

import pyos
from pyos import psh


def cat(*obj_or_ids, representer=None):
    """Convert the contents of objects into strings.
    A representer can optionally be passed in which should take the passed object and convert it to
    a string.
    """
    if not obj_or_ids:
        return None

    hist = mincepy.get_historian()
    _options, rest = pyos.psh_lib.separate_opts(*obj_or_ids)
    to_cat = []

    for entry in rest:
        if isinstance(entry,
                      (str, pyos.PyosPath, pyos.fs.nodes.BaseNode, hist.archive.get_id_type())):
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
