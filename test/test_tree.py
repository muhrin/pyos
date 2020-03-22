from mincepy.testing import Car

from pyos import pyos


def test_tree_basic():
    Car().save()
    results = pyos.tree()
    assert len(results) == 1


def test_tree_depth():
    Car().save()
    pyos.save(Car(), 'sub/')
    pyos.save(Car(), 'sub/sub/')
    pyos.save(Car(), 'sub/sub/sub')

    def check_depth(results):
        depth = 0
        while results:
            results = results[0]
            depth += 1
        return depth

    results = pyos.tree()
    assert check_depth(results) == 4
    for idx in range(4):
        assert check_depth(pyos.tree - pyos.L(idx)()) == idx + 1
