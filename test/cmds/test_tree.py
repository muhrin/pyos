from mincepy.testing import Car

from pyos import pysh


def test_tree_basic():
    Car().save()
    results = pysh.tree()
    assert len(results) == 1


def test_tree_depth():
    Car().save()
    pysh.save(Car(), 'sub/')
    pysh.save(Car(), 'sub/sub/')
    pysh.save(Car(), 'sub/sub/sub')

    def check_depth(results):
        depth = 0
        while results:
            results = results[0]
            depth += 1
        return depth

    results = pysh.tree()
    assert check_depth(results) == 4
    for idx in range(4):
        assert check_depth(pysh.tree - pysh.L(idx)()) == idx + 1
