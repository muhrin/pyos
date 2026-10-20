.. pyos documentation master file, created by
   sphinx-quickstart on Fri Mar 31 17:03:20 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _pyOS: https://github.com/muhrin/pyos
.. _Django: https://www.djangoproject.com/
.. _SQLAlchemy: https://www.sqlalchemy.org/



Welcome to pyOS's documentation!
================================

.. image:: https://github.com/muhrin/pyos/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/muhrin/pyos/actions/workflows/ci.yml
    :alt: CI

.. image:: https://codecov.io/gh/muhrin/pyos/branch/develop/graph/badge.svg
    :target: https://codecov.io/gh/muhrin/pyos
    :alt: Coverage

.. image:: https://img.shields.io/pypi/v/pyos.svg
    :target: https://pypi.python.org/pypi/pyos/
    :alt: Latest Version

.. image:: https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fmuhrin%2Fpyos%2Fdevelop%2Fpyproject.toml
    :target: https://pypi.python.org/pypi/pyos/
    :alt: Python versions

.. image:: https://img.shields.io/pypi/l/pyos.svg
    :target: https://pypi.python.org/pypi/pyos/
    :alt: License


`pyOS`_: A fresh way to interact with your python objects as though they were files on your filesystem.


Features
++++++++

* Familiar shell like interface: ``ls``, ``mv``, ``cat``, ``rm`` but on your objects!
* Powerful and fast ``find`` facility to locate and organise your python world.
* Version control of all your objects by default.
* Familiar flags from the shell e.g. ``ls(-l)``, ``rm(-r)``.
* Easy pipe-like chaining e.g. ``find(meta=dict(name='martin')) | rm``
* Use it from Python (e.g. IPython or Jupyter) or from its own shell, ``pyos shell``.
* Store your objects in a local directory (no server needed) or in MongoDB.

Think of pyOS as a mixture between an ORM like `Django`_ or `SQLAlchemy`_ but where you can store any class by providing
a simple mapper, from then on you interact with your objects as if they were files in a filesystem.
Many of the familiar \*nix commands are available (``ls``, ``mv``, ``rm``, ``tree``, ``cat``,
``find``) except they take on a new, more powerful form because you're in a fully fledged python environment!


Why pyOS?
+++++++++

* **An organised, searchable home for your results**: no more folders of pickle files, save the
  objects themselves into directories and find them by what they contain, without a database
  schema.
* **Lightweight experiment tracking**: tag objects with metadata, find them by it and move the
  interesting ones somewhere safe.
* **Every version kept**: see how any object came to be what it is.
* **Work locally, share with your group**: start with a local database (nothing to install) and
  ``rsync`` what is worth keeping to a shared server.

See :doc:`use-cases` for examples of each.


Installation
++++++++++++

pyOS needs Python 3.11 or later.  Installation with pip:

.. code-block:: shell

    pip install pyos


Installation from git:

.. code-block:: shell

    # via pip
    pip install git+https://github.com/muhrin/pyos.git

    # manually
    git clone https://github.com/muhrin/pyos.git
    cd pyos
    pip install .


Getting started
+++++++++++++++

Tell pyOS where to store objects (see :doc:`basics` for more on connecting):

.. code-block:: shell

    # In a local directory, no server needed
    export MINCEPY_ARCHIVE="litemongo:///path/to/my/db#pyos"

    # Or, in MongoDB, e.g. a server started with: docker run -d -p 27017:27017 mongo
    export MINCEPY_ARCHIVE="mongodb://localhost/pyos"

Then use it from Python:

.. code-block:: python

    from pyos.pyos import *

    ls()

or from the shell, ``pyos shell`` (optionally with ``--uri <archive URI>``).


Development
+++++++++++

Clone the project:

.. code-block:: shell

    git clone https://github.com/muhrin/pyos.git
    cd pyos


Create a new virtual environment for `pyOS`_ (Python 3.11 or later):

.. code-block:: shell

    python3 -m venv env

Install all requirements for `pyOS`_ and the pre-commit hooks (ruff, bandit, etc.):

.. code-block:: shell

    env/bin/pip install -e '.[dev]'
    env/bin/pre-commit install

Types are checked with ty (also run in CI).  Files that don't pass yet are listed under
``[tool.ty.src] exclude`` in ``pyproject.toml``, please remove them from there once fixed:

.. code-block:: shell

    env/bin/ty check

The tests can be run against MongoDB (by default ``mongodb://127.0.0.1``) or, without a server,
using litemongo's in-memory engine:

.. code-block:: shell

    MINCEPY_TEST_URI="litemongo://?engine=memory#pyos-tests" env/bin/pytest test

Table Of Contents
+++++++++++++++++

.. toctree::
   :glob:
   :maxdepth: 3

   use-cases
   basics
   examples/quick-start.ipynb
   examples/restaurants.ipynb
   apidoc


Versioning
++++++++++

This software follows `Semantic Versioning`_


.. _Semantic Versioning: https://semver.org/
