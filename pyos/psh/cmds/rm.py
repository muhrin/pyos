"""The remove command"""
import copy

import tqdm

import pyos
from pyos import psh


def _remove_directories(nodes):
    filtered = pyos.fs.ResultsNode()
    for node in nodes:
        if isinstance(node, pyos.fs.DirectoryNode):
            print("rm: cannot remove '{}': Is a directory".format(node.abspath.name))
        elif isinstance(node, pyos.fs.ResultsNode):
            filtered.extend(_remove_directories(node))
        else:
            filtered.append(copy.copy(node))
    return filtered


@pyos.psh_lib.command(pass_options=True)
@pyos.psh_lib.flag(psh.p, help="show progress bar")
@pyos.psh_lib.flag(psh.r, help="remove directories and their contents recursively")
def rm(options, *obj_or_ids):  # pylint: disable=invalid-name
    """Remove objects"""
    to_delete = psh.ls(-psh.d, *obj_or_ids)
    recursive = options.pop(psh.flags.r)
    if not recursive:
        to_delete = _remove_directories(to_delete)

    if to_delete:
        if options.pop(psh.flags.p):
            to_delete = tqdm.tqdm(to_delete, desc="rm")

        for node in to_delete:
            node.delete()
