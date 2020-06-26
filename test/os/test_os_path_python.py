"""Tests taken from cPython's path tests:
https://github.com/python/cpython/blob/master/Lib/test/test_path.py

Where I've changed a check I've kept the origianl to highlight differences beween pyos and python.
"""
import pytest

from pyos import db
from pyos.os import pos as os
from pyos.os import path


def test_join():
    assert path.join("/foo", "bar", "/bar", "baz") == "/bar/baz"
    assert path.join("/foo", "bar", "baz") == "/foo/bar/baz"
    assert path.join("/foo/", "bar/", "baz/") == "/foo/bar/baz/"


def test_split():
    # original: assert path.split("/foo/bar") == ("/foo", "bar")
    assert path.split("/foo/bar") == ("/foo/", "bar")

    assert path.split("/") == ("/", "")
    assert path.split("foo") == ("", "foo")
    assert path.split("////foo") == ("////", "foo")

    # original: assert path.split("//foo//bar") == ("//foo", "bar")
    assert path.split("//foo//bar") == ("//foo/", "bar")


def test_basename():
    assert path.basename("/foo/bar") == "bar"
    assert path.basename("/") == ""
    assert path.basename("foo") == "foo"
    assert path.basename("////foo") == "foo"
    assert path.basename("//foo//bar") == "bar"


def test_dirname():
    # original: assert path.dirname("/foo/bar") == "/foo"
    assert path.dirname("/foo/bar") == "/foo/"

    assert path.dirname("/") == "/"
    assert path.dirname("foo") == ""
    assert path.dirname("////foo") == "////"

    # original: assert path.dirname("//foo//bar") == "//foo"
    assert path.dirname("//foo//bar") == "//foo/"


def test_expanduser():
    homedir = db.homedir()
    assert path.expanduser("foo") == "foo"
    assert path.expanduser("~") == homedir
    assert path.expanduser("~/") == homedir
    assert path.expanduser("~/foo") == "{}foo".format(homedir)


def test_normpath():
    assert path.normpath("") == "."
    assert path.normpath("/") == "/"

    # orig: assert path.normpath("//") == "//"
    assert path.normpath("//") == "/"

    assert path.normpath("///") == "/"

    # orig: assert path.normpath("///foo/.//bar//") == "/foo/bar"
    assert path.normpath("///foo/.//bar//") == "/foo/bar/"

    assert path.normpath("///foo/.//bar//.//..//.//baz") == "/foo/baz"
    assert path.normpath("///..//./foo/.//bar") == "/foo/bar"


def test_relpath():
    (real_getcwd, os.getcwd) = (os.getcwd, lambda: r"/home/user/bar/")
    try:
        assert os.getcwd() == r"/home/user/bar/"

        curdir = os.path.split(os.getcwd())[-1]
        with pytest.raises(ValueError):
            path.relpath("")

        assert path.relpath("a") == "a"
        assert path.relpath(path.abspath("a")) == "a"
        assert path.relpath("a/b") == "a/b"
        assert path.relpath("../a/b") == "../a/b"

        # orig: assert path.relpath("a", "../b") == "../" + curdir + "/a"
        assert path.relpath("a", "../b") == "../" + curdir + "a"

        # orig: assert path.relpath("a/b", "../c") == "../" + curdir + "/a/b"
        assert path.relpath("a/b", "../c") == "../" + curdir + "a/b"

        assert path.relpath("a", "b/c") == "../../a"
        assert path.relpath("a", "a") == "."
        assert path.relpath("/foo/bar/bat", "/x/y/z") == '../../../foo/bar/bat'
        assert path.relpath("/foo/bar/bat", "/foo/bar") == 'bat'
        assert path.relpath("/foo/bar/bat", "/") == 'foo/bar/bat'
        assert path.relpath("/", "/foo/bar/bat") == '../../..'
        assert path.relpath("/foo/bar/bat", "/x") == '../foo/bar/bat'
        assert path.relpath("/x", "/foo/bar/bat") == '../../../x'
        assert path.relpath("/", "/") == '.'
        assert path.relpath("/a", "/a") == '.'
        assert path.relpath("/a/b", "/a/b") == '.'
    finally:
        os.getcwd = real_getcwd
