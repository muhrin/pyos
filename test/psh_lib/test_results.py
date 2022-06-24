# -*- coding: utf-8 -*-
import pytest

from pyos import psh_lib


def test_caching_results():
    with pytest.raises(TypeError):
        psh_lib.CachingResults(None)

    # Let's check with some proper data this time
    data = list(range(100))
    res = psh_lib.CachingResults(iter(data))
    assert res[0] == 0
    assert res[10] == 10
    with pytest.raises(IndexError):
        _ = res[100]

    # Check with slicing
    res = psh_lib.CachingResults(iter(data))
    assert res[2:5] == [2, 3, 4]

    res = psh_lib.CachingResults(iter(data))
    assert res[:] == data
