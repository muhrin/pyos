.. _documentation: https://pyos.readthedocs.io/en/latest/
.. _litemongo: https://github.com/muhrin/litemongo
.. _mincePy: https://github.com/muhrin/mincepy

pyOS
====

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

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
    :alt: Ruff

A fresh way to interact with your python objects as though they were files on your filesystem.

Installation
------------

pyOS needs Python 3.11 or later:

.. code-block:: shell

    pip install pyos

Objects are stored using mincePy_, either in a local directory (with litemongo_, no server needed)
or in MongoDB.  Tell pyOS where with the ``MINCEPY_ARCHIVE`` environment variable:

.. code-block:: shell

    # In a local directory
    export MINCEPY_ARCHIVE="litemongo:///path/to/my/db#pyos"

    # Or, in MongoDB, e.g. a server started with: docker run -d -p 27017:27017 mongo
    export MINCEPY_ARCHIVE="mongodb://localhost/pyos"

Getting started
---------------

Use pyOS from Python (e.g. IPython or Jupyter):

.. code-block:: python

    In [1]: from pyos.pyos import *
    In [2]: ls()

or from its shell:

.. code-block:: shell

    pyos shell
    # Or choose the database directly, e.g. one in memory to try things out
    pyos shell --uri "litemongo://?engine=memory#scratch"

From here you can ``save()`` objects, use familiar linux commands (``ls()``, ``mv()``, ``find()``,
etc.) and a whole lot more.  Head over to the documentation_ to find out how.
