import pytest

from mincepy.testing import mongodb_archive, historian

import pyos


@pytest.fixture(autouse=True)
def lib(historian):
    pyos.lib.init()
    yield pyos.lib
    pyos.lib.reset()
