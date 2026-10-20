Get to know pyOS
++++++++++++++++

The object system
=================

The object system structure is designed to emulate many of the features familiar in disk based filesystems.  Python objects are stored in directories, with the root of the filesystem starting at '``/``'.

Objects
-------

Objects emulate files as commonly found on disk filesystems.  Some details:

- Every object has a name and exists in a directory.
- Object names within a directory are unique.
- Object names can be any valid string, however it is advantageous to use value python variable names as they can then be used in tab-completion helpers.


Directories
-----------

Directories in pyOS provide a familiar way to organise your objects, just was you would in your filesystem.


Connecting and sessions
-----------------------

pyOS works with a *session*: a connection to a database (a mincePy historian) together with a
current working directory.  Usually there is just one, the global session, and you don't need to
think about it: the first time pyOS is used it connects to the default archive (given by the
``MINCEPY_ARCHIVE`` environment variable, or mincePy's default).  To choose the database yourself:

.. code-block:: python

    import pyos

    pyos.connect("mongodb://localhost/my-db")  # A MongoDB server
    pyos.connect("litemongo:///path/to/dir#my-db")  # A local directory, no server needed
    pyos.connect("litemongo://?engine=memory#scratch")  # In memory, gone when Python exits

The shell takes the same URIs, either from the command line (``pyos shell --uri <uri>``, which
takes precedence over any ``connect`` in the startup script) or with ``connect <uri>`` once in it.

Several sessions can be used at the same time, each with its own database and working directory.
The functions in ``pyos.db`` and ``pyos.fs`` take the session to use, whereas ``pyos.os``,
``pyos.pathlib`` and the shell commands always use the global one:

.. code-block:: python

    with pyos.connect("litemongo:///path/to/backup#my-db", use_globally=False) as backup:
        pyos.db.save_one(car, "my_car", session=backup)
        print(pyos.fs.find(session=backup))


Design decisions
----------------

The guiding principle was to produce something as familiar as possible, but, data integrity, performance and simplicity was prioritised when they would conflict with familiarity.  Performance considerations were prioritised in the following order:

1. Querying.  Finding objects (by state or metadata) should be as fast as possible, including queries involving directory starting points e.g., find all objects with some metadata in the directory ``/home/`` and below.
2. Insertions.  Inserting objects, especially in batches, should be very fast.
3. Deletions.  Deleting objects can be somewhat slow compared to other operations as it is expected to be performed less frequently.

These help to explain the fact a directory and an object can have the same name in the same directory.  The current path of an object is stored in an object's metadata (as a directory and an object name) and there is no explicit representation of a directory (hence why an empty directory cannot exist).
To understand how this results from the above goals consider the situation of having explicit directory objects.

To save a new object in a directory would require loading the directory object, adding our object to it, and re-saving it.
In the meantime, if another client is also saving to that directory we would be blocked until they were done.
This incurs a performance hit when inserting, going against goal 2) above, and makes the code more difficult as an explicit locking mechanism must be put in place.

Ah, but "how can we prevent two objects with the same name existing in the same folder then?", you ask.  Well that's done by having a simple unique index the metadata ensuring that no two objects can share the same directory and name.
This, metadata based, structure also comes with significant query performance benefits because a query looking for data related to particular paths can be performed by making one request to the database that puts a condition on the directory key instead of recursively having to look for a folder, and then querying any subfolders, and their subfolders, etc. all as separate queries.
