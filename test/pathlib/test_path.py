from mincepy.testing import Car

import pyos
from pyos import psh


def test_root():
    """Make sure that root is represented as '/' always"""
    assert str(pyos.pathlib.PurePath('/')) == '/'
    assert str(pyos.pathlib.PurePath('//').resolve()) == '/'


def test_iterdir():
    psh.save(Car(), 'my_car')
    with pyos.pathlib.working_path('sub/'):
        psh.save(Car(), 'my_sub_car')
    cwd = pyos.pathlib.Path()

    content = tuple(map(pyos.Path.name.fget, cwd.iterdir()))
    assert len(content) == 2

    assert 'my_car' in content
    assert 'sub/' in content
