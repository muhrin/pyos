from click.testing import CliRunner
import mincepy.archive_factory
import pytest

from pyos import _globals, cli


@pytest.fixture
def cli_uri(test_utils):
    yield test_utils.create_archive_uri(db_name="pyos-cli-test")
    # The CLI connects globally, so don't leave its session behind for other tests
    _globals.reset_global_session()


def test_psh_uri(cli_uri):
    result = CliRunner().invoke(cli.psh_, ["--uri", cli_uri, "-c", "mkdir garage/; ls"])
    assert result.exit_code == 0, result.output
    assert "garage" in result.output
    assert _globals.get_global_session() is not None


def test_psh_uri_from_environment(cli_uri, monkeypatch):
    monkeypatch.setenv(mincepy.archive_factory.ENV_ARCHIVE_URI, cli_uri)
    result = CliRunner().invoke(cli.psh_, ["-c", "mkdir shed/; ls"])
    assert result.exit_code == 0, result.output
    assert "shed" in result.output


def test_psh_not_connected(monkeypatch):
    """Without a URI the shell should start unconnected (rather than trying a default server)"""
    monkeypatch.delenv(mincepy.archive_factory.ENV_ARCHIVE_URI, raising=False)
    monkeypatch.setattr(_globals, "_GLOBAL_SESSION", None)
    result = CliRunner().invoke(cli.psh_, ["-c", "disconnect"])
    assert result.exit_code == 0, result.output
    assert _globals.get_global_session() is None
