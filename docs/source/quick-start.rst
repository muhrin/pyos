.. _the restaurants example: examples/restaurants.ipynb

Quick Start
===========

This is a quick introduction to PyOS, see `the restaurants example`_ for a more complete example.

.. jupyter-execute::

  from pyos.pyos import *
  from mincepy.testing import Car


Our ``Car`` class has two members, ``make`` and ``colour``, so let's save a couple in the current directory:


.. jupyter-execute::

  pwd()

.. jupyter-execute::

  ls()

.. jupyter-execute::

  ferrari = Car('ferrari', 'red')
  save(ferrari, 'ferrari')
  skoda = Car('skoda', 'green')
  save(skoda, 'skoda')
  ls -l ()

Let's have a look at the cars:

.. jupyter-execute::

  ls | cat


We see some additional properties of the objects used to store them in the database but our colours and makes are there.
Now, let's move them to their own folder...

.. jupyter-execute::

  mv('ferrari', 'skoda', 'garage/')
  ls()

...and set some metadata

.. jupyter-execute::

  meta -s ('garage/ferrari', reg='VD394') # '-s' for set
  meta -s ('garage/skoda', reg='N317')
  meta('garage/ferrari') # This gets our metadata

The metadata can be used to search:

.. jupyter-execute::

  find(meta=dict(reg='VD394')) | locate


Finally, let's clean up.

.. jupyter-execute::

  rm -r ('garage/')
  ls()