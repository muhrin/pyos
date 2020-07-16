from pyos import db
from pyos import os
from pyos import pathlib


def create_empty_file(filename: os.PathSpec):
    hist = db.get_historian()
    file = hist.create_file(os.path.basename(filename))
    db.save_one(file, path=filename)


change_cwd = pathlib.working_path  # pylint: disable=invalid-name
