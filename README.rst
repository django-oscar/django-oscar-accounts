=======
Budgets
=======

.. warning::
    This is a work in progress

This package provides managed budgets for Oscar.  It uses a `double-entry
bookkeeping system`_ where every transaction is recorded twice (once for the
source and once for the destination).

.. _`double-entry bookkeeping system`: http://en.wikipedia.org/wiki/Double-entry_bookkeeping_system

Features:

* Budgets can have:
  - No users assigned
  - A single "primary" user
  - A set of users assigned
* A user can have multiple budgets
* A budget can have a start and end date to allow its usage in a limited time
  window
* A budget has a credit limit which defaults to zero.  Budgets can be set up
  with no credit limit.

Installation
------------

Install using pip and add ``budgets`` to ``INSTALLED_APPS``.  Run syncdb and
you're away.

API
---

Create budget instances using the manager::

    from decimal import Decimal
    import datetime

    from django.contrib.auth.models import User

    from budgets import models

    anonymous_budget = models.Budget.objects.create()
    barry = User.objects.get(username="barry")
    user_budget = models.Budget.objects.create(primary_user=barry)
    
    no_credit_limit_budget = models.Budget.objects.create(credit_limit=None)
    credit_limit_budget = models.Budget.objects.create(credit_limit=Decimal('1000.00'))

    today = datetime.date.today()
    next_week = today + datetime.timedelta(days=7)
    date_limited_budget = models.Budget.objects.create(
        start_date=today, end_date=next_week)

Transfer funds using the facade::

    from budgets import facade

    staff_member = User.objects.get(username="staff")
    facade.transfer(source=no_credit_limit_budget,
                    destination=user_budget,
                    amount=Decimal('10.00'),
                    user=staff_member)

If the proposed transfer is invalid, an exception will be raised.  All
exceptions are subclasses of ``budgets.exceptions.BudgetException``.

Contributing
------------

Fork repo, set-up virtualenv and run::
    
    make install

Run tests with::
    
    ./runtests.py

Got nuts.
