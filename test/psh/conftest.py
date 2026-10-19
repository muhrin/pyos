from typing import Optional

import cmd2
import cmd2.py_bridge
import pytest

from pyos import psh


class PyosShellTester(psh.PyosShell):
    """Shell that can run commands from Python and capture their results (this replaces the
    cmd2-ext-test plugin, which doesn't support cmd2 3+)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pybridge = cmd2.py_bridge.PyBridge(self)

    def app_cmd(self, command: str, echo: Optional[bool] = None) -> cmd2.CommandResult:
        """Run a command as if typed at the prompt, returning its captured output"""
        try:
            self._in_py = True
            return self._pybridge(command, echo=echo)
        finally:
            self._in_py = False

    def fixture_setup(self):
        """Do what cmdloop() does before reading commands"""
        for func in self._preloop_hooks:
            func()
        self.preloop()

    def fixture_teardown(self):
        """Do what cmdloop() does after reading commands"""
        for func in self._postloop_hooks:
            func()
        self.postloop()


@pytest.fixture
def pyos_shell():
    app = PyosShellTester()
    app.fixture_setup()

    # Make sure that exceptions bubble up
    old_pexcept = app.pexcept

    def new_pexcept(*args, **kwargs):
        old_pexcept(*args, **kwargs)
        raise  # noqa: PLE0704 - pexcept is called while handling the exception

    app.pexcept = new_pexcept

    yield app
    app.fixture_teardown()
