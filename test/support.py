import mincepy

import pyos
from pyos import db, os, pathlib


def create_empty_file(filename: os.PathSpec, session: pyos.Session = None):
    session = session or pyos.get_global_session()

    hist: mincepy.Historian = session.historian
    file = hist.create_file(os.path.basename(filename))
    db.save_one(file, path=filename)


change_cwd = pathlib.working_path  # pylint: disable=invalid-name
