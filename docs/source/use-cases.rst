What can I use pyOS for?
++++++++++++++++++++++++

pyOS gives your Python objects a home: a versioned, searchable filesystem that you browse with the
commands you already know.  It is at its best in interactive work, in IPython or Jupyter, wherever
results pile up faster than you can organise them.  Here are some of the things it is good for.

The examples below follow on from one another and use objects of this class (any class can be
stored, see the mincePy_ documentation for how to make your own types savable):

.. code-block:: python

    import uuid

    import mincepy

    from pyos.pyos import *


    class Result(mincepy.ConvenientSavable, type_id=uuid.UUID("0b3b8d51-6f8c-4c2b-9a49-6e2f7c3c9b1a")):
        """The result of a calculation"""

        structure = mincepy.field()
        energy = mincepy.field()

        def __init__(self, structure: str, energy: float):
            super().__init__()
            self.structure = structure
            self.energy = energy


An organised, searchable home for your results
==============================================

Instead of folders of pickle files (``results_v3_final/run_17.pkl``), save the objects themselves
into directories and find them again by what they contain, without designing a database schema
first:

.. code-block:: python

    mkdir("projects/alloys/")
    cd("projects/alloys/")
    for name, energy in (("CuZn", -3.5), ("CuAu", -2.9), ("NiAl", -3.3)):
        save(Result(name, energy), name)

    ls()  # CuZn  CuAu  NiAl
    find(Result.energy < -3.2)  # CuZn  NiAl

Objects can refer to each other, and because the database is shared safely between processes,
several scripts or notebooks can save to it at the same time.


Lightweight experiment tracking
===============================

Tag objects with metadata (parameters, code versions, status...), find them by it and move the
interesting ones somewhere for safe keeping:

.. code-block:: python

    meta -s ("CuZn", method="dft", status="converged")
    meta -s ("CuAu", method="dft", status="failed")
    meta -s ("NiAl", method="ml", status="converged")

    converged = find(meta=dict(status="converged"))  # CuZn  NiAl
    mkdir("../curated/")
    mv(converged, "../curated/")

Unlike tools that only log numbers and files, what you get back are the objects themselves.


Every version kept
==================

Every time an object is saved a new version is recorded, so you can always see how a result came
to be what it is:

.. code-block:: python

    cd("../curated/")
    cuzn = load("CuZn")
    cuzn.energy = -3.6
    cuzn.save()

    history(cuzn, representer=lambda result: f"{result.structure}: {result.energy}")
    # CuZn: -3.5
    # CuZn: -3.6


Work locally, share with your group
===================================

Start on your laptop with a database in a local directory (litemongo_, nothing to install), then
copy what is worth keeping to a database that your group shares, e.g. on a MongoDB server where
everyone has their own ``/home/<user>/`` and works together in ``/shared/``:

.. code-block:: python

    shared = "litemongo:///path/to/shared/db#group"  # Or e.g. mongodb://server/group
    rsync("./", f"{shared}/shared/alloys/")

``rsync`` only copies what has changed, and can also copy the objects' histories (``history=True``)
and metadata (``meta="update"``).


A friendlier way to work with a database
========================================

People who would never write a database query can still organise and tidy up their data, either
from Python or from the shell (``pyos shell``), using commands they already know: ``ls``, ``cd``,
``mv``, ``rm``, ``find``, ``cat``, ``meta``...  Entering ``ipy`` from the shell gives an IPython
session with all of these commands ready to use.


.. _mincePy: https://mincepy.readthedocs.io/
.. _litemongo: https://github.com/muhrin/litemongo
