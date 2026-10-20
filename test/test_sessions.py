"""Tests for sessions: that several can be used side by side, that the library layers use the
session they are given (rather than the global one) and how the global session is chosen"""

import mincepy
import mincepy.archive_factory
import mincepy.history
from mincepy.testing import Car
import pytest

import pyos
from pyos import _globals, db, fs, psh


@pytest.fixture
def other_session(test_utils):
    """A second session, with its own database and working directory, that is not the global one"""
    with test_utils.temporary_session("pyos-other-session") as (_uri, session):
        db.fs.make_dirs(("/", "elsewhere"), exists_ok=True, session=session)
        session.set_cwd(("/", "elsewhere"))
        yield session


def _found(session) -> set:
    """The ids of all the objects that have a path in the given session"""
    return {node.obj_id for node in fs.find("/", session=session)}


def test_sessions_are_independent(session, other_session):
    assert _globals.get_global_session() is session
    car = Car()
    car_id = db.save_one(car, "car", session=other_session)

    assert car_id in _found(other_session)
    assert car_id not in _found(session)
    assert other_session.historian.get_obj_id(car) == car_id
    assert session.historian.get_obj_id(car) is None

    # Each has its own working directory
    assert other_session.cwd == ("/", "elsewhere")
    assert session.cwd != other_session.cwd


def test_relative_paths_use_the_sessions_cwd(other_session):
    car_id = db.save_one(Car(), "car", session=other_session)
    assert db.get_paths(car_id, session=other_session)[0].path == "/elsewhere/car"
    assert list(db.get_obj_id_from_path("car", session=other_session)) == [car_id]

    db.rename(car_id, "renamed", session=other_session)
    assert db.get_paths(car_id, session=other_session)[0].path == "/elsewhere/renamed"


def test_library_uses_the_given_session(other_session):
    car = Car()
    car_id = db.save_one(car, "car", meta={"reg": 123}, session=other_session)

    assert db.load(car_id, session=other_session) is car
    assert db.to_obj_id(car, session=other_session) == car_id
    assert db.get_meta(car_id, session=other_session) == {"reg": 123}

    db.update_meta(car_id, meta={"colour": "red"}, session=other_session)
    assert db.get_meta(car_id, session=other_session) == {"reg": 123, "colour": "red"}
    db.set_meta(car_id, meta={"reg": 456}, session=other_session)
    assert db.get_meta(car_id, session=other_session) == {"reg": 456}
    assert dict(db.find_meta({"reg": 456}, session=other_session)) == {car_id: {"reg": 456}}

    db.set_paths((car_id, "/elsewhere/moved"), session=other_session)
    assert db.get_paths(car_id, session=other_session)[0].path == "/elsewhere/moved"


def test_find_starts_in_the_sessions_cwd(other_session):
    car_id = db.save_one(Car(), "car", session=other_session)
    db.save_one(Car(), "/outside_cwd", session=other_session)
    assert [node.obj_id for node in fs.find(session=other_session)] == [car_id]


def test_session_save(session, other_session):
    car = Car()
    car_id = other_session.save(car, "car")
    assert other_session.historian.get_obj_id(car) == car_id
    assert session.historian.get_obj_id(car) is None
    assert db.get_paths(car_id, session=other_session)[0].path == "/elsewhere/car"


def test_nodes_keep_their_session(other_session):
    car = Car()
    car_id = db.save_one(car, "car", session=other_session)

    node = fs.to_node(pyos.pathlib.PurePath("/elsewhere/car"), session=other_session)
    assert isinstance(node, fs.ObjectNode)
    assert node.obj_id == car_id
    assert node.obj is car
    # Converting a node to a node is a no-op, also when given a session
    assert fs.to_node(node, session=other_session) is node


def test_listener_uses_its_own_session(session, other_session):
    """Objects saved directly through a session's historian get a path in *that* session"""
    car = Car()
    car_id = other_session.historian.save(car)
    assert db.get_paths(car_id, session=other_session)[0].path == f"/elsewhere/{car_id}"
    assert car_id not in _found(session)

    other_session.historian.delete(car)
    assert car_id not in _found(other_session)


def test_context_manager(test_utils):
    uri = test_utils.create_archive_uri(db_name="pyos-session-ctx")
    with pyos.connect(uri, use_globally=False) as session:
        historian = session.historian
        assert _globals.get_global_session() is not session

    # Once closed, the session no longer gives new objects paths
    car_id = historian.save(Car())
    with pyos.connect(uri, use_globally=False) as fresh:
        assert car_id not in _found(fresh)


@pytest.fixture
def no_session(monkeypatch, test_utils):
    """Start without a pyOS session or a global mincePy historian, with MINCEPY_ARCHIVE pointing at
    a test archive"""
    uri = test_utils.create_archive_uri(db_name="pyos-auto-connect")
    monkeypatch.setenv(mincepy.archive_factory.ENV_ARCHIVE_URI, uri)
    monkeypatch.setattr(_globals, "_GLOBAL_SESSION", None)
    monkeypatch.setattr(mincepy.history, "CURRENT_HISTORIAN", None)
    yield
    _globals.reset_global_session()


@pytest.mark.usefixtures("no_session")
def test_auto_connect():
    assert _globals.get_global_session(create=False) is None

    # Using pyOS connects to the default archive
    assert pyos.os.getcwd()
    session = _globals.get_global_session(create=False)
    assert session is not None
    assert session.historian.archive.database.name == "pyos-auto-connect"
    assert _globals.get_global_session() is session


@pytest.mark.usefixtures("no_session")
def test_auto_connect_uses_global_historian(historian):
    """If there is a global mincePy historian, pyOS uses that rather than connecting again"""
    mincepy.set_historian(historian)
    assert _globals.get_global_session().historian is historian


@pytest.mark.usefixtures("no_session")
def test_checking_for_a_session_does_not_connect():
    assert _globals.get_global_session(create=False) is None
    shell = psh.PyosShell(skip_intro=True)
    assert shell.prompt == "[not connected]$ "
    assert _globals.get_global_session(create=False) is None
