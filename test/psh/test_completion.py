# -*- coding: utf-8 -*-
from mincepy.testing import Car

import pyos.os
from pyos import psh


def test_completion_simple():
    pyos.os.makedirs('/test/sub/')

    psh.cd('/test')
    psh.save(Car(), 'my_car')
    psh.cd('sub/')
    Car().save()

    comp = psh.completion.PathCompletion('/test/')
    content = tuple(comp.__dir__())
    assert len(content) == 2
    assert 'sub' in content
    assert 'my_car' in content

    assert isinstance(getattr(comp, 'sub'), psh.completion.PathCompletion)
    assert isinstance(getattr(comp, 'my_car'), psh.completion.PathCompletion)
    assert set(comp._ipython_key_completions_()) == {'sub', 'my_car'}  # pylint: disable=protected-access

    # Check __repr__
    assert psh.completion.PathCompletion.__name__ in repr(comp)
    assert comp.__fspath__() in repr(comp)

    # Check for non-existent paths
    assert not list(psh.completion.PathCompletion('/does_not_exist/').__dir__())
