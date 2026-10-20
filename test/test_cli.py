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


def _database_name() -> str:
    return _globals.get_global_session().historian.archive.database.name


def test_psh_uri_overrides_startup_script(app_dir, test_utils, cli_uri):
    """A URI given on the command line should take precedence over connecting in the startup
    script (which would otherwise also be a wait if it points to a server that isn't running)"""
    script_uri = test_utils.create_archive_uri(db_name="pyos-cli-startup")
    (app_dir / "pshrc").write_text(f"connect {script_uri}\n")

    result = CliRunner().invoke(cli.psh_, ["--uri", cli_uri, "-c", "pwd"])
    assert result.exit_code == 0, result.output
    assert "Skipping 'connect" in result.output
    assert _database_name() == "pyos-cli-test"

    # Without a URI on the command line the startup script connects as usual
    result = CliRunner().invoke(cli.psh_, ["-c", "pwd"])
    assert result.exit_code == 0, result.output
    assert _database_name() == "pyos-cli-startup"
