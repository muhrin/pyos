import inspect

from pyos.psh_lib import opts


def my_fn():
    """This is my docstring"""


def my_other_fn():
    """My other docstring"""


def test_command_docstring():
    command = opts.Command(my_fn)
    doc = inspect.getdoc(command.__call__)
    assert doc == 'This is my docstring'

    other_command = opts.Command(my_other_fn)
    doc = inspect.getdoc(other_command.__call__)
    assert doc == 'My other docstring'


def test_command_name():
    command = opts.Command(my_fn)
    assert command.name == "my_fn"
