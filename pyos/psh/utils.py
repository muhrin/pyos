import collections
import concurrent.futures
import contextlib
import io
import logging
import os
import threading
from typing import Optional, Any, Dict

_LOGGER = logging.getLogger(__name__)


class ThreadStreamRedirector:
    """Idea for this was found here:
    https://stackoverflow.com/questions/14890997/redirect-stdout-to-a-file-only-for-a-specific-thread
    """

    def __init__(self, *, default: Optional[io.TextIOBase] = None, name=''):
        self.default = default
        self._streams = {}
        self._name = name

    def register(self, stream: Optional[io.TextIOBase]):
        identity = threading.current_thread().ident
        _LOGGER.debug("(%s): Redirecting thread %s to %s", self._name, identity, stream)
        self._streams[identity] = stream

    def unregister(self):
        identity = threading.current_thread().ident
        _LOGGER.debug("(%s): Unregistering thread %s", self._name, identity)
        self._streams.pop(identity)

    @contextlib.contextmanager
    def redirect(self, stream: Optional[io.TextIOBase]):
        self.register(stream)
        yield
        self.unregister()

    def __iter__(self):
        return self._get_stream().__iter__()

    def __next__(self):
        return self._get_stream().__next__()

    def close(self):
        stream = self._get_stream()
        return stream.close()

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

    def _get_stream(self):
        identity = threading.current_thread().ident
        try:
            return self._streams[identity]
        except KeyError:
            return self.default


PipeInfo = collections.namedtuple('PipeInfo', 'pipe_in pipe_out')


class PipingCommands:
    """
    Object used to keep track of pipes and a pool of threads associated to commands that are piping
    from one to another.
    """

    def __init__(self) -> None:
        self._thread_pool = concurrent.futures.ThreadPoolExecutor()
        self._pipes = {}  # type: Dict[Any, PipeInfo]
        self._futures = []

    def create_pipe(self, label) -> PipeInfo:
        read_fd, write_fd = os.pipe()
        pipe_info = PipeInfo(open(write_fd, 'w'), open(read_fd, 'r'))

        # Insert the new pipe info
        if label in self._pipes:
            self._close_pipe(label)
        self._pipes[label] = pipe_info

        return pipe_info

    def get_pipe(self, idx: int) -> PipeInfo:
        return self._pipes[idx]

    def submit(self, func, *args, **kwargs):
        future = self._thread_pool.submit(func, *args, **kwargs)
        self._futures.append(future)
        return future

    def send_sigint(self) -> None:
        """Send a SIGINT to the process similar to if <Ctrl>+C were pressed"""
        self._thread_pool.shutdown(wait=False)
        self._close_all_pipes()

    def terminate(self) -> None:
        """Terminate the process"""
        self._thread_pool.shutdown(wait=False)
        self._close_all_pipes()

    def wait(self) -> None:
        """Wait for the process to finish"""
        self._thread_pool.shutdown(wait=True)
        self._close_all_pipes()

    def _close_all_pipes(self):
        _LOGGER.debug("Closing all pipes")
        for label in list(self._pipes):
            self._close_pipe(label)

    def _close_pipe(self, label):
        try:
            pipe_in, pipe_out = self._pipes.pop(label)
        except KeyError:
            pass
        else:
            pipe_in.close()
            pipe_out.close()
