import argparse
import functools
import logging
import os
import subprocess
import sys
from typing import List, Optional

import mincepy
import cmd2.constants
import cmd2.plugin
import cmd2.utils

from pyos import db
from pyos import os as pos
from pyos import version
from . import constants
from . import utils

_LOGGER = logging.getLogger(__name__)

__all__ = 'PyosShell', 'mod'


def mod() -> str:
    """Get the message of the day string"""
    banner_lines = version.LOGO.split("\n")
    max_line_length = max(map(len, banner_lines))

    second_column = [
        '',
        'Documentation: https://pyos.readthedocs.io/',
        '',
        '',
        "Powered by mincePy (v{})".format(mincepy.__version__),  # pylint: disable=no-member,
        'Version {}'.format(version.__version__)
    ]
    second_column.extend([''] * (len(banner_lines) - len(second_column)))

    message = []
    for banner, info in zip(banner_lines, second_column):
        fmt_string = "{{:<{}}} | {{}}".format(max_line_length)
        message.append(fmt_string.format(banner, info))
    message.append('\n')
    return "\n".join(message)


class PyosShell(cmd2.Cmd):
    """The pyOS shell"""

    def __init__(self,
                 startup_script='',
                 startup_commands: Optional[List[str]] = None,
                 skip_intro=False):

        hist_path = os.path.join(utils.get_app_dir(), constants.HISTORY_FILE)
        startup_script = startup_script or os.path.join(utils.get_app_dir(), constants.STARTUP_FILE)
        super().__init__(startup_script=startup_script,
                         allow_cli_args=False,
                         use_ipython=True,
                         persistent_history_file=hist_path)

        if startup_commands:
            self._startup_commands.extend(startup_commands)

        for cmd_set in utils.plugins_get_commands():
            self.register_command_set(cmd_set)

        self.default_to_shell = True

        if not skip_intro:
            self.intro = mod()
        self._update_prompt()
        self.register_cmdfinalization_hook(self.command_finalise)

    @classmethod
    def execute(cls, *cmd, **kwarg):
        """Run the passed commands and return"""
        init_args = dict(skip_intro=True)
        init_args.update(kwarg)
        cmd = list(cmd) + ['quit']
        init_args['startup_commands'] = cmd
        app = PyosShell(**init_args)
        app.cmdloop()

    def command_finalise(
            self, data: cmd2.plugin.CommandFinalizationData) -> cmd2.plugin.CommandFinalizationData:
        self._update_prompt()
        return data

    def _update_prompt(self):
        try:
            historian = db.get_historian()
        except RuntimeError:
            # Happens when there is a global historian but pyos.db.init() hasn't been called
            historian = None

        if historian is None:
            self.prompt = '[not connected]$ '
        else:
            self.prompt = "{}$ ".format(pos.getcwd())

    def _redirect_output(self, statement: cmd2.Statement) -> cmd2.utils.RedirectionSavedState:
        if statement.pipe_to:
            # Initialize the redirection saved state
            saved = self._create_redirection_save()

            _LOGGER.debug("Attempting piped command:\n"
                          "%s\n"
                          "stdin=%s, stdout=%s", statement.pipe_to, saved.saved_sys_stdin,
                          saved.saved_self_stdout)

            funcs = []
            for part in statement.pipe_to.split(cmd2.constants.REDIRECTION_PIPE):
                # Parse the command
                # Whitespace (especially at beginning) confuses parsing to statement
                part = part.strip()
                part_statement = self._input_line_to_statement(part)
                funcs.append(functools.partial(self.onecmd, part_statement))

            thread_proc = utils.Piper(funcs, out_stream=self.stdout)
            self.stdout = thread_proc.out_redirector
            self.stdin = thread_proc.in_redirector
            saved.redirecting = True

            try:
                self._cur_pipe_proc_reader = thread_proc
                self._redirecting = True
                thread_proc.start()
            except Exception:
                # Shut down the full pipe
                thread_proc.shutdown(wait=True)
                # Restore the default streams
                self._restore_output(statement, saved)
                raise

            return saved

        return super(PyosShell, self)._redirect_output(statement)

    # Preserve quotes since we are passing these strings to the shell
    @cmd2.with_argparser(cmd2.Cmd.shell_parser, preserve_quotes=True)
    def do_shell(self, args: argparse.Namespace) -> None:
        """Execute a command as if at the OS prompt"""
        # Create a list of arguments to shell
        tokens = [args.command] + args.command_args

        # Expand ~ where needed
        cmd2.utils.expand_user_in_tokens(tokens)
        expanded_command = ' '.join(tokens)

        # Prevent KeyboardInterrupts while in the shell process. The shell process will
        # still receive the SIGINT since it is in the same process group as us.
        with self.sigint_protection:
            # For any stream that is a StdSim, we will use a pipe so we can capture its output

            kwargs = dict(
                stdin=sys.stdin if self._redirecting else None,
                # Pass standard input if redirecting
                stdout=subprocess.PIPE
                if isinstance(self.stdout, cmd2.utils.StdSim) else self.stdout,
                stderr=subprocess.PIPE if isinstance(sys.stderr, cmd2.utils.StdSim) else sys.stderr,
                shell=True)

            _LOGGER.debug("Starting shell command: %s. Capturing stdin: %s", expanded_command,
                          self._redirecting)
            proc = subprocess.Popen(expanded_command, **kwargs)

            proc_reader = cmd2.utils.ProcReader(proc, self.stdout, sys.stderr)
            proc_reader.wait()

            # Save the return code of the application for use in a pyscript
            self.last_result = proc.returncode

    def _create_redirection_save(self):
        """Save the current state of the steams and members related to redirection"""
        return utils.RedirectionSavedState(self.stdout, sys.stdout, self.stdin, sys.stdin,
                                           self._cur_pipe_proc_reader, self._redirecting)

    def _restore_output(self, statement: cmd2.Statement,
                        saved_redir_state: utils.RedirectionSavedState):
        """Handles restoring state after output redirection

        :param statement: Statement object which contains the parsed input from the user
        :param saved_redir_state: contains information needed to restore state data
        """
        if saved_redir_state.redirecting:
            # If we redirected output to the clipboard
            if statement.output and not statement.output_to:
                # Fallback to default behaviour
                super(PyosShell, self)._restore_output(statement, saved_redir_state)
            else:
                # Check if we need to wait for the process being piped
                if self._cur_pipe_proc_reader is not None:
                    self._cur_pipe_proc_reader.wait()

                self.stdout = saved_redir_state.saved_self_stdout
                sys.stdout = saved_redir_state.saved_sys_stdout
                self.stdin = saved_redir_state.saved_self_stdin
                sys.stdin = saved_redir_state.saved_sys_stdin
                self._cur_pipe_proc_reader = saved_redir_state.saved_pipe_proc_reader
                self._redirecting = saved_redir_state.saved_redirecting
        else:
            super(PyosShell, self)._restore_output(statement, saved_redir_state)

        if isinstance(saved_redir_state, utils.RedirectionSavedState):
            sys.stdin = saved_redir_state.saved_sys_stdin


if __name__ == '__main__':
    sys.exit(PyosShell().cmdloop())
