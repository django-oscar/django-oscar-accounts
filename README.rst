=======
Budgets
=======

.. warning::
    This is a work in progress

This package provides managed budgets for Oscar.  It uses a `double-entry
bookkeeping system`_ where every transaction changes two accounts.

.. _`double-entry bookkeeping system`: http://en.wikipedia.org/wiki/Double-entry_bookkeeping_system

accounting to ensure all transaction have a source and destination.

Features:

* A budget can have:
  - No users assigned
  - A single "primary" user
  - A set of users assigned
* A user can have multiple budgets
* A budget can have a start and end date to allow its usage in a limited time
  window
* A budget has a credit limit which defaults to zero.  Budgets can be set up
  with no credit limit.

TODO:

* Make top-level models abstract for extensibility

Contributing
------------

Fork repo, set-up virtualenv and run::
    
    make install

Run tests with::
    
    ./runtests.py
