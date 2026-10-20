import pyos
from pyos import _globals


def test_connect_disconnect(pyos_shell, test_utils):
    uri = test_utils.create_archive_uri(db_name="pyos-connect-test")

    res = pyos_shell.app_cmd(f"connect {uri}")
    assert f"Connected to {uri}" in res.stdout
    session = _globals.get_global_session()
    assert session is not None
    assert pyos_shell.prompt != "[not connected]$ "

    res = pyos_shell.app_cmd("disconnect")
    assert not res.stderr
    assert _globals.get_global_session(create=False) is None
    assert pyos_shell.prompt == "[not connected]$ "


def test_disconnect_when_not_connected(pyos_shell, historian):
    # Use a separate session, the one from the fixtures is closed by them
    pyos.init(historian)
    pyos_shell.app_cmd("disconnect")
    assert _globals.get_global_session(create=False) is None

    # Disconnecting again shouldn't fail
    res = pyos_shell.app_cmd("disconnect")
    assert "Not connected" in res.stderr
