"""The tree command"""
import pyos
from . import flags
from .. import opts
from .ls import ls


@opts.option(flags.L)
def tree(options, *paths):
    """Get a tree representation of the given paths"""
    to_tree = ls(-flags.d, *paths)
    level = options.pop(flags.L, -1)
    # Fully expand all directories
    for dir_node in to_tree.directories:
        dir_node.expand(level)
    to_tree.show(mode=pyos.TREE_VIEW)
    return to_tree
