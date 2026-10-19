import contextlib
import os
import random
import string
from typing import ContextManager, Generator

import mincepy.testing as mince_testing

import pyos

ENV_ARCHIVE_URI = "PYOS_TEST_URI"

# The test backend is chosen the same way as for mincepy (MINCEPY_TEST_URI or MINCEPY_TEST_BASE_URI),
# so these work with MongoDB as well as litemongo
get_base_uri = mince_testing.get_base_uri
create_archive_uri = mince_testing.create_archive_uri


def get_archive_uri() -> str:
    return os.environ.get(ENV_ARCHIVE_URI) or create_archive_uri(db_name="pyos-tests")


@contextlib.contextmanager
def temporary_session(db_name: str = "") -> Generator[tuple[str, pyos.Session], None, None]:
    """Create a temporary database using the base archive URI and the given db name or a random one.  Yields a tuple
    consisting of the archive uri and the historian"""
    archive_uri = mince_testing.create_archive_uri(get_base_uri(), db_name)
    with mince_testing.temporary_historian(archive_uri) as historian:
        session = pyos.init(historian, use_globally=False)
        yield archive_uri, session
