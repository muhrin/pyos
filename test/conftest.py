# -*- coding: utf-8 -*-
import os

from mincepy.testing import historian, mongodb_archive  # pylint: disable=unused-import
import pytest

import pyos
import pyos.db

from . import utils

# pylint: disable=redefined-outer-name


@pytest.fixture
def archive_base_uri() -> str:
    return utils.get_base_uri()


@pytest.fixture
def archive_uri():
    return os.environ.get(utils.ENV_ARCHIVE_URI, utils.DEFAULT_ARCHIVE_URI)


@pytest.fixture(autouse=True)
def lib(historian):  # pylint: disable=unused-argument
    pyos.init()
    yield pyos.db.lib
    pyos.reset()


@pytest.fixture
def test_utils():
    return utils
