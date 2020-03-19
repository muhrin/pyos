from pyos import pyos
from pyos import dirs


def test_reaching_root():
    """Assert the correct behaviour when traversing up until reaching root and beyond"""
    path = dirs.PyosPath()
    cwd = dirs.cwd()
    for _ in range(len(cwd.parts) - 1):
        pyos.cd('..')

    # Should be at root
    assert dirs.cwd() == dirs.PyosPath('/')

    # Now trying going up again
    pyos.cd('..')
    # Should still be at root
    assert dirs.cwd() == dirs.PyosPath('/')
