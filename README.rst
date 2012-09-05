===========================
Managed accounts for Django
===========================

This package provides managed accounts for Django.  A managed account is an
allocation of money that can be debited and credited.  Accounts
can be used to implement:

* Giftcard schemes
* Loyalty schemes
* User "credits" that are allocated by sales reps to their customers (more of a
  B2B thing)

Basically anything that involves tracking the movement of funds within a closed
system.

It uses `double-entry bookkeeping`_ where every transaction is recorded
twice (once for the source and once for the destination).  This ensures the
books always balance and there is full audit trail of all transactional
activity.

Despite having 'Oscar' in the name, this package does not import Oscar's classes
and so can be used standalone.

.. _`Oscar`: https://github.com/tangentlabs/django-oscar
.. _`double-entry bookkeeping`: http://en.wikipedia.org/wiki/Double-entry_bookkeeping_system

Features:

* A account has a credit limit which defaults to zero.  Accounts can be set up
  with no credit limit so that they are a 'source' of money within the system.
  At least one account must be set up without a credit limit.
* Accounts can have:
  - No users assigned
  - A single "primary" user - this is the most common case
  - A set of users assigned
* A user can have multiple accounts
* A account can have a start and end date to allow its usage in a limited time
  window
* Accounts can be categorised

Installation
------------

Install using pip and add ``accounts`` to ``INSTALLED_APPS``.  Run syncdb and
you're away.

API
---

Create account instances using the manager::

    from decimal import Decimal
    import datetime

    from django.contrib.auth.models import User

    from accounts import models

    anonymous_account = models.Account.objects.create()

    barry = User.objects.get(username="barry")
    user_account = models.Account.objects.create(primary_user=barry)
    
    no_credit_limit_account = models.Account.objects.create(credit_limit=None)
    credit_limit_account = models.Account.objects.create(credit_limit=Decimal('1000.00'))

    today = datetime.date.today()
    next_week = today + datetime.timedelta(days=7)
    date_limited_account = models.Account.objects.create(
        start_date=today, end_date=next_week)

Transfer funds using the facade::

    from accounts import facade

    staff_member = User.objects.get(username="staff")
    trans = facade.transfer(source=no_credit_limit_account,
                            destination=user_account,
                            amount=Decimal('10.00'),
                            user=staff_member)

Reverse transfers::

    facade.reverse(trans, user=staff_member, 
                   description="Just an example")

If the proposed transfer is invalid, an exception will be raised.  All
exceptions are subclasses of ``accounts.exceptions.AccountException``.  Your
client code should look for exceptions of this type and handle them
appropriately.
 
Client code should only use the ``accounts.models.Budget`` class and the
two functions from ``accounts.facade`` - nothing else should be required.

Contributing
------------

Fork repo, set-up virtualenv and run::
    
    make install

Run tests with::
    
    ./runtests.py
