"""Module that tests the pyOS shell piping functionality"""
import argparse
import sys
import tempfile

import cmd2


class Echo(cmd2.CommandSet):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', dest='tag', type=str, default='anon', help='the tag')
    parser.add_argument('msg', default=None, type=str, nargs='*')

    @cmd2.with_argparser(parser)
    def do_echo(self, args):  # pylint: disable=no-self-use
        if not args.msg:
            # Read from stdin
            args.msg = [line.rstrip() for line in sys.stdin.readlines()]
            if not args.msg:
                args.msg.append('')

        print("{}: {}".format(args.tag, args.msg[0]))


def test_shell_piping(pyos_shell):
    pyos_shell.unregister_command_set(Echo())
    res = pyos_shell.app_cmd('echo -t 1 hello_from_1 | echo -t 2 | echo -t 3')
    assert not res.stderr
    assert res.stdout == '3: 2: 1: hello_from_1\n'


def test_host_shell_piping(pyos_shell, monkeypatch):
    # Mock standard in using a file as pytest effectively disable it
    with tempfile.TemporaryFile() as temp_buffer:
        monkeypatch.setattr('sys.stdin', temp_buffer)

        pyos_shell.do_set('debug true')
        pyos_shell.unregister_command_set(Echo())
        res = pyos_shell.app_cmd("!echo 'shell: hello_from_shell' | echo -t 2 | echo -t 3")
        assert not res.stderr
        assert res.stdout == '3: 2: shell: hello_from_shell\n'

        # Now try shell command in the middle
        res = pyos_shell.app_cmd('echo -t 1 hello_from_1 | !cat | echo -t 3')
        assert not res.stderr
        assert res.stdout == '3: 1: hello_from_1\n'
