from mincepy.testing import Car

from pyos import cmds


def test_tree_basic():
    Car().save()
    results = cmds.tree()
    assert len(results) == 1


def test_tree_depth():
    Car().save()
    cmds.save(Car(), 'sub/')
    cmds.save(Car(), 'sub/sub/')
    cmds.save(Car(), 'sub/sub/sub')

    def check_depth(results):
        depth = 0
        while results:
            results = results[0]
            depth += 1
        return depth

    results = cmds.tree()
    assert check_depth(results) == 4
    for idx in range(4):
        assert check_depth(cmds.tree - cmds.L(idx)()) == idx + 1
