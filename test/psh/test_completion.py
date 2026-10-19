import importlib

from mincepy.testing import Car

from pyos import psh
import pyos.os


def test_completion_simple():
    pyos.os.makedirs("/test/sub/")

    psh.cd("/test")
    psh.save(Car(), "my_car")
    psh.cd("sub/")
    Car().save()

    comp = psh.completion.PathCompletion("/test/")
    content = tuple(dir(comp))
    assert len(content) == 2
    assert "sub" in content
    assert "my_car" in content

    assert isinstance(comp.sub, psh.completion.PathCompletion)
    assert isinstance(comp.my_car, psh.completion.PathCompletion)
    assert set(comp._ipython_key_completions_()) == {
        "sub",
        "my_car",
    }

    # Check __repr__
    assert psh.completion.PathCompletion.__name__ in repr(comp)
    assert pyos.os.fspath(comp) in repr(comp)

    # Check for non-existent paths
    assert not list(dir(psh.completion.PathCompletion("/does_not_exist/")))


def test_shell_path_completion(pyos_shell):
    """cmd2 passes the CommandSet that owns a command to its completers, check that completion
    still works and updates the state of the shell itself"""
    cd_module = importlib.import_module("pyos.psh.cmds.cd")

    pyos.os.makedirs("/test/sub/")
    psh.cd("/test")
    psh.save(Car(), "my_car")
    command_set = pyos_shell.find_commandsets(cd_module.Cd)[0]

    assert psh.completion.dir_completer(command_set, "su", "cd su", 3, 5) == ["sub"]
    # A directory can be completed further, so the shell shouldn't add a space after it
    assert pyos_shell.allow_appended_space is False

    assert psh.completion.file_completer(command_set, "my", "cat my", 4, 6) == ["my_car"]
    assert sorted(psh.completion.path_complete(command_set, "", "ls ", 3, 3)) == ["my_car", "sub"]
