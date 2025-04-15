import contextlib
import os
import random
import string
from typing import ContextManager, Generator

import mincepy.testing as mince_testing

import pyos

ENV_ARCHIVE_BASE_URI = "MINCEPY_TEST_BASE_URI"
DEFAULT_ARCHIVE_BASE_URI = "mongodb://localhost"
ENV_ARCHIVE_URI = "PYOS_TEST_URI"
DEFAULT_ARCHIVE_URI = "mongodb://localhost/pyos-tests"


def get_base_uri() -> str:
    return os.environ.get(ENV_ARCHIVE_BASE_URI, DEFAULT_ARCHIVE_BASE_URI)


def create_archive_uri(base_uri="", db_name=""):
    """Get an archive URI based on the current archive base URI plus the passed database name.

    If the database name is missing a random one will be used"""
    if not db_name:
        letters = string.ascii_lowercase
        db_name = "mincepy-" + "".join(random.choice(letters) for _ in range(5))
    base_uri = base_uri or get_base_uri()
    return base_uri + "/" + db_name


@contextlib.contextmanager
def temporary_session(db_name: str = "") -> Generator[tuple[str, pyos.Session], None, None]:
    """Create a temporary database using the base archive URI and the given db name or a random one.  Yields a tuple
    consisting of the archive uri and the historian"""
    archive_uri = mince_testing.create_archive_uri(get_base_uri(), db_name)
    with mince_testing.temporary_historian(archive_uri) as historian:
        session = pyos.init(historian, use_globally=False)
        yield archive_uri, session
