"""Checks on the project itself: that the documentation builds and its examples run, that the
packages contain what they should and that the project metadata is consistent"""

import importlib.util
import pathlib
import shutil
import socket
import subprocess  # nosec
import sys
import tarfile
import tomllib
import zipfile

import pytest
import yaml

import pyos

ROOT = pathlib.Path(__file__).parents[1]
DOCS = ROOT / "docs" / "source"
EXAMPLES = DOCS / "examples"
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text())


def _has_internet(host="raw.githubusercontent.com") -> bool:
    try:
        socket.create_connection((host, 443), timeout=5).close()
        return True
    except OSError:
        return False


@pytest.mark.parametrize(
    "notebook",
    [
        "quick-start.ipynb",
        pytest.param(
            "restaurants.ipynb",
            marks=pytest.mark.skipif(not _has_internet(), reason="downloads its data"),
        ),
    ],
)
def test_example_notebooks_run(notebook, tmp_path, monkeypatch):
    """The example notebooks should run from start to finish (in a fresh database)"""
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")

    # The kernel inherits the environment: use an in-memory database and keep away from the
    # user's pyOS configuration
    monkeypatch.setenv("MINCEPY_ARCHIVE", f"litemongo://?engine=memory#{tmp_path.name}")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    nb = nbformat.read(EXAMPLES / notebook, as_version=4)
    client = nbclient.NotebookClient(
        nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(tmp_path)}}
    )
    client.execute()


def test_docs_build(tmp_path):
    """The docs should build without warnings (the notebooks are run by the test above)"""
    pytest.importorskip("sphinx")
    pytest.importorskip("nbsphinx")
    if shutil.which("pandoc") is None:
        pytest.skip("nbsphinx needs pandoc")
    result = subprocess.run(  # nosec
        [sys.executable, "-m", "sphinx", "-q", "-W", "--keep-going", "-b", "html"]
        + ["-D", "nbsphinx_execute=never", str(DOCS), str(tmp_path / "html")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_docs_version():
    """The docs should report the version of pyOS"""
    spec = importlib.util.spec_from_file_location("docs_conf", DOCS / "conf.py")
    assert spec is not None and spec.loader is not None
    conf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(conf)
    assert conf.release == pyos.__version__


def test_packages_contain_the_sources(tmp_path):
    builders = pytest.importorskip("hatchling.builders.sdist")
    wheel_builders = pytest.importorskip("hatchling.builders.wheel")

    sdist = next(builders.SdistBuilder(str(ROOT)).build(directory=str(tmp_path)))
    with tarfile.open(sdist) as archive:
        names = {name.split("/", 1)[1] for name in archive.getnames() if "/" in name}
    assert "src/pyos/__init__.py" in names
    assert "src/pyos/psh/shell.py" in names
    assert "README.rst" in names

    wheel = next(wheel_builders.WheelBuilder(str(ROOT)).build(directory=str(tmp_path)))
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    assert "pyos/__init__.py" in names
    assert "pyos/psh/shell.py" in names


def _classifier_versions() -> list[str]:
    prefix = "Programming Language :: Python :: 3."
    return [
        classifier.rsplit(" :: ", 1)[1]
        for classifier in PYPROJECT["project"]["classifiers"]
        if classifier.startswith(prefix)
    ]


def test_python_versions_are_consistent():
    """The supported Python versions are given in several places, they should all agree"""
    versions = _classifier_versions()
    oldest = versions[0]
    assert versions == sorted(versions, key=lambda version: tuple(map(int, version.split("."))))

    assert PYPROJECT["project"]["requires-python"] == f">={oldest}"
    assert PYPROJECT["tool"]["ruff"]["target-version"] == "py" + oldest.replace(".", "")
    assert PYPROJECT["tool"]["ty"]["environment"]["python-version"] == oldest

    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text())
    tested = workflow["jobs"]["tests"]["strategy"]["matrix"]["python-version"]
    assert tested == versions


@pytest.mark.parametrize(
    "path", ["README.rst", "docs/source/index.rst", "docs/source/basics.rst", "docs/source/conf.py"]
)
def test_docs_have_no_stale_references(path):
    """References to services and files the project no longer uses"""
    text = (ROOT / path).read_text().lower()
    for stale in ("travis", "coveralls", "setup.py", "archive/master.zip"):
        assert stale not in text, f"'{stale}' found in {path}"
