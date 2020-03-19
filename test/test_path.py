from pyos import pyos
from pyos import dirs


def test_reaching_root():
    """Assert the correct behaviour when traversing up until reaching root and beyond"""
    cwd = dirs.cwd()
    for _ in range(len(cwd.parts) - 1):
        pyos.cd('..')

    # Should be at root
    assert dirs.cwd() == dirs.PyosPath('/')

    # Now trying going up again
    pyos.cd('..')
    # Should still be at root
    assert dirs.cwd() == dirs.PyosPath('/')


def test_saving_path():
    path = dirs.PyosPath('/some/random/path/')
    path_str = str(path)
    obj_id = pyos.save(path)
    del path

    loaded = pyos.load(obj_id)
    assert str(loaded) == path_str
