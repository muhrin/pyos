from mincepy.testing import Car

from pyos import cmd


def test_tree_basic():
    Car().save()
    results = cmd.tree()
    assert len(results) == 1


def test_tree_depth():
    Car().save()
    cmd.save(Car(), 'sub/')
    cmd.save(Car(), 'sub/sub/')
    cmd.save(Car(), 'sub/sub/sub')

    def check_depth(results):
        depth = 0
        while results:
            results = results[0]
            depth += 1
        return depth

    results = cmd.tree()
    assert check_depth(results) == 4
    for idx in range(4):
        assert check_depth(cmd.tree - cmd.L(idx)()) == idx + 1
