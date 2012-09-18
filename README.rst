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
activity.  Your finance people will thank you.

Despite having 'Oscar' in the name, this package does not import Oscar's classes
and so can be used standalone.  At some point, it may provide helper modules for
making integration with Oscar easier.

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
* An account can have a start and end date to allow its usage in a limited time
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

Error handling
--------------

Note that the transfer operation is wrapped in its own database transaction to
ensure that only complete transfers are written out.  When using Django's
transaction middleware, you need to be careful.  If you have an unhandled
exception,  then account transfers will still be committed even though nothing
else will be.  To handle this, you need to make sure that, if an exception
occurs during your post-payment code, then you roll-back any transfers.

Here's a toy example::

    from accounts import facade

    def submit(self, order_total):
        # Take payment first
        transfer = facade.transfer(self.get_user_account(),
                                   self.get_merchant_account(),
                                   order_total)
        # Create order models
        try:
            self.place_order()
        except Exception, e:
            # Something went wrong placing the order.  Roll-back the previous
            # transfer
            facade.reverse(transfer)

In this situation, you'll end up with two transfers being created but no order.
While this isn't ideal, it's the best way of handling exceptions that occur
during order placement.

Settings
--------

ACCOUNTS_SOURCE_NAME = 'Merchant'


Contributing
------------

Fork repo, set-up virtualenv and run::
    
    make install

Run tests with::
    
    ./runtests.py
