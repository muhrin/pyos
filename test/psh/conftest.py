# -*- coding: utf-8 -*-
import cmd2_ext_test
import pytest

from pyos import psh


class PyosShellTester(cmd2_ext_test.ExternalTestMixin, psh.PyosShell):
    """Shell tester"""


@pytest.fixture
def pyos_shell():
    app = PyosShellTester()
    app.fixture_setup()

    # Make sure that exceptions bubble up
    old_pexcept = app.pexcept

    def new_pexcept(*args, **kwargs):
        old_pexcept(*args, **kwargs)
        raise  # pylint: disable=misplaced-bare-raise

    app.pexcept = new_pexcept

    yield app
    app.fixture_teardown()
