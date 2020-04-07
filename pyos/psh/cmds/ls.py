"""List command"""
import logging

import mincepy

import pyos
from pyos import psh

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


@pyos.psh_lib.flag(psh.l)
@pyos.psh_lib.flag(psh.d)
@pyos.psh_lib.flag(psh.p)
def ls(*args) -> pyos.fs.ResultsNode:  # pylint: disable=invalid-name
    """List the contents of a directory

    :type: restrict listing to a particular type
    """
    options = args[0]
    rest = list(args[1:])
    parsed = pyos.psh_lib.parse_args(*rest)

    results = pyos.fs.ResultsNode()
    if rest:
        for entry in parsed:
            if isinstance(entry, Exception):
                raise entry

            try:
                results.append(pyos.fs.to_node(entry))
            except mincepy.NotFound as exc:
                logger.info(str(exc))
    else:
        results.append(pyos.fs.to_node(pyos.pathlib.Path()))

    if not options.pop(psh.d):
        for entry in results:
            if isinstance(entry, pyos.fs.DirectoryNode):
                entry.expand(populate_objects=psh.l in options)

        if len(results) == 1 and isinstance(results[0], pyos.fs.DirectoryNode):
            sole_dir = results[0]
            new_results = pyos.fs.ResultsNode(sole_dir.name)
            for result in tuple(sole_dir.children):
                result.parent = new_results

            results = new_results

    if options.pop(psh.l):
        properties = ['loaded', 'type', 'version', 'mtime', 'name']
        if options.pop(psh.p):
            properties.append('str')
        results.show(*properties, mode=pyos.fs.TABLE_VIEW)
    else:
        results.show(mode=pyos.fs.LIST_VIEW)

    return results
