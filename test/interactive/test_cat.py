import mincepy
import mincepy.testing

import pyos
import pyos.interactive


def test_cat_file(historian: mincepy.Historian):
    dawg = historian.create_file('dawg.txt')
    dawg.write_text("'sup dawg?")
    file_id = pyos.pyos.save(dawg, 'dawg.txt')

    # Should be able to cat in these various ways, by default cat will print the file contents
    for descriptor in (
            dawg,
            'dawg.txt',  # Relative path string
            pyos.PyosPath('dawg.txt'),  # Relative pyos path
            pyos.PyosPath('dawg.txt').resolve(),  # Abs pyos path
            str(pyos.PyosPath('dawg.txt').resolve()),  # Abs pyos path str
            file_id,  # Obj id
    ):
        catted = pyos.pyos.cat(descriptor)
        assert len(catted) == 1
        assert catted[0] == "'sup dawg?"


def test_cat_object():
    yellow = mincepy.testing.Car('ferrari', 'yellow')
    black = mincepy.testing.Car('ferrari', 'black')
    pyos.pyos.save(yellow, black)

    default_representer = pyos.interactive.representers.get_default()

    catted = pyos.interactive.cat(yellow, black)
    assert len(catted) == 2
    assert catted[0] == default_representer(yellow)
    assert catted[1] == default_representer(black)


def test_cat_empty():
    pyos.lib.save_one(mincepy.testing.Car())
    results = pyos.interactive.cat()
