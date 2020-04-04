"""List command"""
import logging

import mincepy

import pyos
from . import flags

logger = logging.getLogger(__name__)


@pyos.opts.flag(flags.l)
@pyos.opts.flag(flags.d)
@pyos.opts.flag(flags.p)
def ls(*args) -> pyos.ResultsNode:  # pylint: disable=invalid-name
    """List the contents of a directory

    :type: restrict listing to a particular type
    """
    options = args[0]
    rest = list(args[1:])
    parsed = pyos.utils.parse_args(*rest)

    results = pyos.ResultsNode()
    if rest:
        for entry in parsed:
            if isinstance(entry, Exception):
                raise entry

            try:
                results.append(pyos.to_node(entry))
            except mincepy.NotFound as exc:
                logger.info(str(exc))
    else:
        results.append(pyos.to_node(pyos.dirs.cwd()))

    if not options.pop(flags.d):
        for entry in results:
            if isinstance(entry, pyos.DirectoryNode):
                entry.expand(populate_objects=flags.l in options)

        if len(results) == 1 and isinstance(results[0], pyos.DirectoryNode):
            sole_dir = results[0]
            new_results = pyos.ResultsNode(sole_dir.name)
            for result in tuple(sole_dir.children):
                result.parent = new_results

            results = new_results

    if options.pop(flags.l):
        properties = ['loaded', 'type', 'version', 'mtime', 'name']
        if options.pop(flags.p):
            properties.append('str')
        results.show(*properties, mode=pyos.TABLE_VIEW)
    else:
        results.show(mode=pyos.LIST_VIEW)

    return results
