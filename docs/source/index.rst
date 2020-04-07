.. pyos documentation master file, created by
   sphinx-quickstart on Fri Mar 31 17:03:20 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _pyOS: https://github.com/muhrin/pyos


Welcome to pyOS's documentation!
================================

.. image:: https://codecov.io/gh/muhrin/pyos/branch/develop/graph/badge.svg
    :target: https://codecov.io/gh/muhrin/pyos
    :alt: Coveralls

.. image:: https://travis-ci.org/muhrin/pyos.svg
    :target: https://travis-ci.org/muhrin/pyos
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


`pyOS`_: A fresh way to interact with your python objects as though they were files on your filesystem.


Features
++++++++

* Familiar shell like interface: ``ls``, ``mv``, ``cat``, ``rm`` but on your objects!
* Powerful and fast ``find`` facility to locate and organise your python world.
* Version control of all your objects by default.
* Familiar flags from the shell e.g. ``ls (-l)``, ``cp(-n)``.
* Easy pipe-like chaining e.g. ``rm(find(meta={'name': 'martin'}))``

PyOS allows you to treat python objects in a
similar way to the way you interact with files on your filesystem at the moment except in an ``ipython``
console or script.  Objects are stored in a database and presented to the user as existing in a
virtual file system.  Many of the familiar \*nix commands are available (``ls``, ``mv``, ``rm``, ``tree``, ``cat``,
``find``) except they take on a new, more powerful form because you're in a fully fledged python environment
and not restricted to just two types (file and directories) like on a traditional filesystem but
indeed any python type that can be stored by PyOS' backend.


Installation
++++++++++++

Installation with pip:

.. code-block:: shell

    pip install pyos


Installation from git:

.. code-block:: shell

    # via pip
    pip install https://github.com/muhrin/pyos/archive/master.zip

    # manually
    git clone https://github.com/muhrin/pyos.git
    cd pyos
    python setup.py install


Development
+++++++++++

Clone the project:

.. code-block:: shell

    git clone https://github.com/muhrin/pyos.git
    cd pyos


Create a new virtualenv for `pyOS`_:

.. code-block:: shell

    virtualenv -p python3 pyos

Install all requirements for `pyOS`_:

.. code-block:: shell

    env/bin/pip install -e '.[dev]'

Table Of Contents
+++++++++++++++++

.. toctree::
   :glob:
   :maxdepth: 3

   examples/restaurants.ipynb
   apidoc


Versioning
++++++++++

This software follows `Semantic Versioning`_


.. _Semantic Versioning: http://semver.org/

