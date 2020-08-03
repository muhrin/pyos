import cmd2_ext_test
import pytest

from pyos import psh


class PyosShellTester(cmd2_ext_test.ExternalTestMixin, psh.PyosShell):
    """Shell tester"""


@pytest.fixture
def pyos_shell():
    app = PyosShellTester()
    app.fixture_setup()
    yield app
    app.fixture_teardown()
