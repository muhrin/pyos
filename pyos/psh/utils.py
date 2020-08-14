import collections
import concurrent.futures
import contextlib

try:
    from contextlib import nullcontext
except ImportError:
    from contextlib2 import nullcontext
import io
import logging
import os
import sys
import threading
import traceback
from typing import Optional, Union, TextIO, List, Callable, Tuple

import click
import cmd2.utils
import stevedore

_LOGGER = logging.getLogger(__name__)


class ThreadStreamRedirector(io.TextIOBase):
    """Idea for this was found here:
    https://stackoverflow.com/questions/14890997/redirect-stdout-to-a-file-only-for-a-specific-thread
    """

    def __init__(self, *, default: Optional[TextIO] = None, name=''):
        super().__init__()
        self.default = default
        self._streams = {}
        self._name = name

    def register(self, stream: Optional[TextIO]):
        identity = threading.current_thread().ident
        _LOGGER.debug("(%s): Redirecting thread %s to %s", self._name, identity, stream)
        self._streams[identity] = stream

    def unregister(self):
        identity = threading.current_thread().ident
        _LOGGER.debug("(%s): Unregistering thread %s", self._name, identity)
        self._streams.pop(identity)

    @contextlib.contextmanager
    def redirect(self, stream: Optional[TextIO]):
        self.register(stream)
        yield
        self.unregister()

    def __iter__(self):
        return self._get_stream().__iter__()

    def __next__(self):
        return self._get_stream().__next__()

    @property
    def closed(self) -> bool:
        return self._get_stream().closed

    def close(self):
        if getattr(self, '_finalizing', False):
            # We're being asked to close because of finalising but because we don't own any streams
            # ourselves, we just redirect, we are not responsible for closing them in this case.
            return

        stream = self._get_stream()
        logging.debug("Closing stream %s", stream)
        if stream.name == '<stdin>':
            logging.warning("Someone is closing the standard input: \n%s",
                            ''.join(traceback.format_stack()))
        stream.close()

    def write(self, message):
        stream = self._get_stream()
        logging.debug("Writing %s from thread %s to %s", message,
                      threading.current_thread().ident, stream)
        stream.write(message)

    def read(self, size=-1):
        return self._get_stream().read(size=size)

    def readline(self):
        return self._get_stream().readline()

    def readlines(self):
        return self._get_stream().readlines()

    def flush(self):
        self._get_stream().flush()

    def seek(self, offset, whence=io.SEEK_SET):
        return self._get_stream().seek(offset, whence=whence)

    def tell(self):
        return self._get_stream().tell()

    def isatty(self):
        return self._get_stream().isatty()

    def fileno(self):
        return self._get_stream().fileno()

    def _get_stream(self):
        identity = threading.current_thread().ident
        try:
            return self._streams[identity]
        except KeyError:
            return self.default


class Piper:

    def __init__(self, funcs: List[Callable], out_stream: TextIO = sys.stdout):
        self._funcs = funcs
        self._out_stream = out_stream

        self._pipes = {}
        self._in_steam = None
        self._thread_pool = None
        self._orig_stdin = sys.stdin
        self._orig_stdout = sys.stdout

        # Open up the 0th pipe and set up our input stream
        _read, write = self._get_pipe(0)
        self._in_steam = open(write, 'w')

        # Input/Output redirectors
        self._in_redir = ThreadStreamRedirector(name='stdin', default=self._orig_stdin)
        self._out_redir = ThreadStreamRedirector(name='stdout', default=self._orig_stdout)

    @property
    def in_stream(self) -> TextIO:
        return self._in_steam

    @property
    def in_redirector(self) -> TextIO:
        return self._in_redir

    @property
    def out_redirector(self) -> TextIO:
        return self._out_redir

    def start(self, capture_this_stdout=True, capture_all_stdout=False):
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(256)
        try:
            # Start redirecting standard streams
            sys.stdin = self._in_redir
            sys.stdout = self._out_redir

            if capture_this_stdout:
                # On this thread, redirect standard out to our input stream
                self._out_redir.register(self._in_steam)
            if capture_all_stdout:
                self._out_redir.default = self._in_steam

            for idx, func in reversed(list(enumerate(self._funcs))):
                # Create a pipe at the INPUT side of this func
                read, _write = self._get_pipe(idx)

                # OUTPUT: Determine what the output stream for this part should be
                if idx == len(self._funcs) - 1:
                    # At the end, so just go to standard out
                    open_out_stream = nullcontext(self._out_stream)
                else:
                    # Need to output to the next commands input
                    _next_read, next_write = self._pipes[idx + 1]
                    open_out_stream = open(next_write, 'w')

                done_redirecting = threading.Event()

                future = self._thread_pool.submit(self._run_func, func, open(read, 'r'),
                                                  open_out_stream, done_redirecting)

                try:
                    done_redirecting.wait(timeout=0.1)
                except TimeoutError:
                    # Try checking the future first
                    future.result(timeout=0.)

                    # Didn't raise, so we need to raise ourselves
                    raise RuntimeError("Failed to redirect streams for command '{}' in a timely "
                                       "manner".format(func))
                else:
                    del done_redirecting

        except Exception:
            self.shutdown(wait=True)
            raise

    def shutdown(self, wait=True):
        """Shutdown the pipe processor and clean up"""
        if self._thread_pool is None:
            return

        _LOGGER.debug("Shutting down pipe processor")

        # First thing is to close the input stream as this will cause it to flush
        # and downstream commands may still be waiting for input
        try:
            self._in_steam.close()
        except BrokenPipeError:
            _LOGGER.debug("Broken pipe error")

        _LOGGER.debug("Waiting for thread pool to shut down")
        self._thread_pool.shutdown(wait=wait)
        if self._thread_pool is None:
            # Another thread already beat us to it
            return

        _LOGGER.debug("Thread pool shut down")

        self._in_steam = None
        sys.stdin = self._orig_stdin
        sys.stdout = self._orig_stdout
        self._orig_stdin = None
        self._orig_stdout = None
        self._in_redir = None
        self._out_redir = None

        self._funcs = None
        self._pipes = None
        self._thread_pool = None

    # region Cmd2 compatibility
    def send_sigint(self):
        """Send a SIGINT to the process similar to if <Ctrl>+C were pressed"""
        self.shutdown(wait=False)

    def terminate(self):
        """Terminate the process"""
        self.shutdown(wait=False)

    def wait(self):
        """Wait for the process to finish"""
        self.shutdown()

    # endregion

    def _run_func(self, func, open_in_stream, open_out_stream, done_redirecting: threading.Event):
        """
        Run a function that is part of the pipe.

        :param func: the function to invoke.  Will be called without any arguments
        :param open_in_stream: the input stream for the function
        :param open_out_stream: the output stream for the function
        :param done_redirecting: an event that tells the caller that redirection has been set up
        :return: the return value of the func()
        """
        with open_in_stream as in_stream, open_out_stream as out_stream:
            with self._in_redir.redirect(in_stream), self._out_redir.redirect(out_stream):
                done_redirecting.set()
                return func()

    def _get_pipe(self, idx) -> Tuple:
        try:
            pipe = self._pipes[idx]
        except KeyError:
            pipe = os.pipe()
            self._pipes[idx] = pipe
            _LOGGER.debug("Created pipe %s for func %s", pipe, self._funcs[idx])

        return pipe


PipeInfo = collections.namedtuple('PipeInfo', 'pipe_in pipe_out')


class RedirectionSavedState(cmd2.utils.RedirectionSavedState):
    """Extension of cmd2's standard redirection saved state to support additional properties"""

    # pylint: disable=too-few-public-methods

    # pylint: disable=too-many-arguments
    def __init__(self, self_stdout: Union[cmd2.utils.StdSim,
                                          TextIO], sys_stdout: Union[cmd2.utils.StdSim, TextIO],
                 self_stdin: TextIO, sys_stdin: TextIO,
                 pipe_proc_reader: Optional[cmd2.utils.ProcReader], saved_redirecting: bool):
        super().__init__(self_stdout, sys_stdout, pipe_proc_reader, saved_redirecting)
        self.saved_self_stdin = self_stdin
        self.saved_sys_stdin = sys_stdin


PLUGINS_COMMANDS_NS = 'pyos.plugins.shell'


def plugins_get_commands() -> List:
    """Get all plugins that implement pyOS shell commands"""
    mgr = stevedore.extension.ExtensionManager(
        namespace=PLUGINS_COMMANDS_NS,
        invoke_on_load=False,
    )

    commands = []

    def get_command(extension: stevedore.extension.Extension):
        try:
            commands.extend(extension.plugin())
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Failed to get command plugin from %s", extension.name)

    try:
        mgr.map(get_command)
    except stevedore.extension.NoMatches:
        pass

    return commands


def get_app_dir() -> str:
    """Get the absolute path to the pyOS configuration file on disk.
    This will be in the standard location for that OS e.g. on linux ~/.config/pyos/"""
    return click.get_app_dir('pyos')
