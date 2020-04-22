import pyos


def test_root():
    """Make sure that root is represented as '/' always"""
    assert str(pyos.pathlib.PurePath('/')) == '/'
    assert str(pyos.pathlib.PurePath('//').resolve()) == '/'
