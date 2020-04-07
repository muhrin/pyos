import pytest

from mincepy.testing import historian, mongodb_archive

import pyos


@pytest.fixture(autouse=True)
def lib(historian):
    pyos.init()
    yield pyos.db.lib
    pyos.reset()
