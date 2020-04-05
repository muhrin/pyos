import mincepy
import mincepy.testing

import pyos
from pyos import cmds


def test_cat_file(historian: mincepy.Historian):
    dawg = historian.create_file('dawg.txt')
    dawg.write_text("'sup dawg?")
    file_id = cmds.save(dawg, 'dawg.txt')

    # Should be able to cat in these various ways, by default cat will print the file contents
    for descriptor in (
            dawg,
            'dawg.txt',  # Relative path string
            pyos.PyosPath('dawg.txt'),  # Relative pyos path
            pyos.PyosPath('dawg.txt').resolve(),  # Abs pyos path
            str(pyos.PyosPath('dawg.txt').resolve()),  # Abs pyos path str
            file_id,  # Obj id
    ):
        catted = cmds.cat(descriptor)
        assert catted == "'sup dawg?", "Problem with {}".format(descriptor)


def test_cat_object():
    yellow = mincepy.testing.Car('ferrari', 'yellow')
    black = mincepy.testing.Car('ferrari', 'black')
    cmds.save(yellow, black)

    default_representer = pyos.representers.get_default()

    catted = cmds.cat(yellow, black)
    assert len(catted) == 2
    assert catted[0] == default_representer(yellow)
    assert catted[1] == default_representer(black)


def test_cat_empty():
    pyos.lib.save_one(mincepy.testing.Car())
    result = cmds.cat()
    assert result is None
