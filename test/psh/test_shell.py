import IPython

import pyos
from pyos import psh


def test_ipy_has_psh_commands(pyos_shell, monkeypatch):
    """Entering ipy from the shell should make the psh commands available straight away (issue #8)"""
    namespaces = []
    # cmd2 imports start_ipython from IPython when ipy is run, so replace it there
    monkeypatch.setattr(
        IPython, "start_ipython", lambda **kwargs: namespaces.append(kwargs["user_ns"])
    )
    pyos_shell.onecmd_plus_hooks("ipy")

    (namespace,) = namespaces
    for name in psh.__all__:
        assert namespace[name] is getattr(psh, name)
    assert namespace["ls"] is psh.ls
    assert namespace["Path"] is pyos.pathlib.Path
