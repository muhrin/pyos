import os

from mincepy.testing import historian, mongodb_archive
import pytest

import pyos
import pyos.db
import pyos.psh.utils

from . import utils


@pytest.fixture
def archive_base_uri() -> str:
    return utils.get_base_uri()


@pytest.fixture
def archive_uri():
    return utils.get_archive_uri()


@pytest.fixture(autouse=True)
def app_dir(tmp_path, monkeypatch):
    """Keep the shell away from the user's own pyos configuration (startup script and history)"""
    path = tmp_path / "pyos-config"
    path.mkdir()
    monkeypatch.setattr(pyos.psh.utils, "get_app_dir", lambda: str(path))
    return path


@pytest.fixture(autouse=True)
def session(historian):  # noqa: F811
    session = pyos.init(historian)
    yield session
    session.close()


# @pytest.fixture(autouse=True)
# def lib(
#     # flake8: noqa: F811
#     historian,
# ):
#     pyos.init()
#     yield pyos.db.lib
#     pyos.reset()


@pytest.fixture
def test_utils():
    return utils
