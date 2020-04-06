from mincepy.testing import Car

from pyos import psh


def test_tree_basic():
    Car().save()
    results = psh.tree()
    assert len(results) == 1


def test_tree_depth():
    Car().save()
    psh.save(Car(), 'sub/')
    psh.save(Car(), 'sub/sub/')
    psh.save(Car(), 'sub/sub/sub')

    def check_depth(results):
        depth = 0
        while results:
            results = results[0]
            depth += 1
        return depth

    results = psh.tree()
    assert check_depth(results) == 4
    for idx in range(4):
        assert check_depth(psh.tree - psh.L(idx)()) == idx + 1
