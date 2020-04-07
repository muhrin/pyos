import mincepy
import mincepy.testing

import pyos
from pyos import psh


def test_cat_file(historian: mincepy.Historian):
    dawg = historian.create_file('dawg.txt')
    dawg.write_text("'sup dawg?")
    file_id = psh.save(dawg, 'dawg.txt')

    # Should be able to cat in these various ways, by default cat will print the file contents
    for descriptor in (
            dawg,
            'dawg.txt',  # Relative path string
            pyos.pathlib.Path('dawg.txt'),  # Relative pyos path
            pyos.pathlib.Path('dawg.txt').resolve(),  # Abs pyos path
            str(pyos.pathlib.Path('dawg.txt').resolve()),  # Abs pyos path str
            file_id,  # Obj id
    ):
        catted = psh.cat(descriptor)
        assert catted == "'sup dawg?", "Problem with {}".format(descriptor)


def test_cat_object():
    yellow = mincepy.testing.Car('ferrari', 'yellow')
    black = mincepy.testing.Car('ferrari', 'black')
    psh.save(yellow, black)

    default_representer = pyos.psh_lib.get_default()

    catted = psh.cat(yellow, black)
    assert len(catted) == 2
    assert catted[0] == default_representer(yellow)
    assert catted[1] == default_representer(black)


def test_cat_empty():
    pyos.db.lib.save_one(mincepy.testing.Car())
    result = psh.cat()
    assert result is None
