.. _documentation: https://pyos.readthedocs.io/en/latest/

pyOS
====

.. image:: https://codecov.io/gh/muhrin/pyos/branch/develop/graph/badge.svg
    :target: https://codecov.io/gh/muhrin/pyos
    :alt: Coverage

.. image:: https://travis-ci.com/muhrin/pyos.svg?branch=master
    :target: https://travis-ci.com/github/muhrin/pyos
    :alt: Travis CI

.. image:: https://img.shields.io/pypi/v/pyos.svg
    :target: https://pypi.python.org/pypi/pyos/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/wheel/pyos.svg
    :target: https://pypi.python.org/pypi/pyos/

.. image:: https://img.shields.io/pypi/pyversions/pyos.svg
    :target: https://pypi.python.org/pypi/pyos/

.. image:: https://img.shields.io/pypi/l/pyos.svg
    :target: https://pypi.python.org/pypi/pyos/

A fresh way to interact with your python objects as though they were files on your filesystem.

Installation
------------

As easy as:

1. Install MongoDB

   Ubuntu:


.. code-block:: shell

    sudo apt install mongodb

2. Install pyos:

.. code-block:: shell

    pip install pyos

3. Jump in to the shell:

.. code-block:: shell

    > ipython

    In [1]: from pyos.pyos import *
    In [2]: ls()


From here you can `save()` objects, use familiar linux commands (`ls()`, `mv()`, `find()`, etc) and a whole lot more.  Head over to the documentation_ to find out how.