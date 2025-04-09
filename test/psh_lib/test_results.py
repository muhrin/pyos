import pytest

import pyos


def test_caching_results():
    with pytest.raises(TypeError):
        pyos.results.CachingResults(None)

    # Let's check with some proper data this time
    data = list(range(100))
    res = pyos.results.CachingResults(iter(data))
    assert res[0] == 0
    assert res[10] == 10
    with pytest.raises(IndexError):
        _ = res[100]

    # Check with slicing
    res = pyos.results.CachingResults(iter(data))
    assert res[2:5] == [2, 3, 4]

    res = pyos.results.CachingResults(iter(data))
    assert res[:] == data
