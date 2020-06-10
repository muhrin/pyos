import os

from mincepy.testing import historian, mongodb_archive  # pylint: disable=unused-import
import pytest

import pyos

ENV_ARCHIVE_URI = 'PYOS_TEST_URI'
DEFAULT_ARCHIVE_URI = 'mongodb://localhost/pyos-tests'

# pylint: disable=redefined-outer-name


@pytest.fixture
def archive_uri():
    return os.environ.get(ENV_ARCHIVE_URI, DEFAULT_ARCHIVE_URI)


@pytest.fixture(autouse=True)
def lib(historian):  # pylint: disable=unused-argument
    pyos.init()
    yield pyos.db.lib
    pyos.reset()
