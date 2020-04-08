"""The tree command"""
import pyos
from pyos import psh


@pyos.psh_lib.command(pass_options=True)
@pyos.psh_lib.option(psh.flags.L)
def tree(options, *paths):
    """Get a tree representation of the given paths"""
    to_tree = psh.ls(-psh.d, *paths)
    level = options.pop(psh.L, -1)
    # Fully expand all directories
    for dir_node in to_tree.directories:
        dir_node.expand(level)
    to_tree.show(mode=pyos.fs.TREE_VIEW)
    return to_tree
