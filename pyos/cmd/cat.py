import pyos
from .ls import ls
from . import flags


def cat(*obj_or_ids, representer=None):
    """Convert the contents of objects into strings.
    A representer can optionally be passed in which should take the passed object and convert it to
    a string.
    """
    _options, rest = pyos.opts.separate_opts(*obj_or_ids)
    to_load = ls(-flags.d, *rest)

    representer = representer or pyos.representers.get_default()

    def iterator():
        for node in to_load:
            if isinstance(node, pyos.DirectoryNode):
                yield "cat: {}: Is a directory".format(node.abspath.name)
            else:
                try:
                    yield representer(node.obj)
                except Exception as exc:  # pylint: disable=broad-except
                    yield representer(exc)

    return pyos.CachingResults(iterator())
