"""Change directory command"""

import pyos


def cd(path: pyos.fs.PathSpec):  # pylint: disable=invalid-name
    path = pyos.PyosPath(path)
    if path.is_file():
        # Assume they just left out the slash
        path = path.to_dir()

    pyos.fs.cd(path)
