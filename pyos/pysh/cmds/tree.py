"""The tree command"""
import pyos
from pyos import pysh


@pyos.shell.option(pysh.flags.L)
def tree(options, *paths):
    """Get a tree representation of the given paths"""
    to_tree = pysh.ls(-pysh.d, *paths)
    level = options.pop(pysh.L, -1)
    # Fully expand all directories
    for dir_node in to_tree.directories:
        dir_node.expand(level)
    to_tree.show(mode=pyos.fs.TREE_VIEW)
    return to_tree
