=======
Budgets
=======

.. warning::
    This is a work in progress

This package provides managed budgets for Oscar.  It uses double-ledger account
to ensure all transaction have a source and destination.

Features:

* A user can have multiple budgets
* A budget can be assigned to either a primary user or a group of other users
* A budget can have a start and end date to allow its usage in a limited time
  window

TODO:

* Make top-level models abstract for extensibility
