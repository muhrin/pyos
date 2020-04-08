"""The remove command"""

import tqdm

import pyos
from pyos import psh


@pyos.psh_lib.command(pass_options=True)
@pyos.psh_lib.flag(psh.p, help="show progress bar")
@pyos.psh_lib.flag(psh.r, help="remove directories and their contents recursively")
def rm(options, *obj_or_ids):  # pylint: disable=invalid-name
    """Remove objects"""
    to_delete = psh.ls(-psh.d, *obj_or_ids)

    if to_delete:
        if options.pop(psh.flags.p):
            to_delete = tqdm.tqdm(to_delete, desc="rm")

        recursive = options.pop(psh.flags.r)
        for node in to_delete:
            if not recursive and isinstance(node, pyos.fs.DirectoryNode):
                print("rm: cannot remove '{}': Is a directory".format(node.abspath.name))
            else:
                node.delete()
