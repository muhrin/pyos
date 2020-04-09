"""Change directory command"""

import pyos


@pyos.psh_lib.command()
def cd(path: pyos.os.PathSpec):  # pylint: disable=invalid-name
    """Change the current working directory"""
    path = pyos.pathlib.PurePath(path)
    if path.is_file_path():
        # Assume they just left out the slash
        path = path.to_dir()

    pyos.os.chdir(path)
