===========================
Managed accounts for Django
===========================

This package provides managed accounts for Django.  A managed account is an
allocation of money that can be debited and credited.  Accounts
can be used to implement:

* Giftcard schemes
* Web accounts
* Loyalty schemes
* User "credits" that are allocated by sales reps to their customers (more of a
  B2B thing)

Basically anything that involves tracking the movement of funds within a closed
system.

It uses `double-entry bookkeeping`_ where every transaction is recorded
twice (once for the source and once for the destination).  This ensures the
books always balance and there is full audit trail of all transactional
activity.  Your finance people will thank you.

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

Install using pip and add ``accounts`` to ``INSTALLED_APPS``.  Add the following
settings:

* ``ACCOUNTS_SOURCE_NAME`` - The name of the 'source' account which is used to
  transfer funds to other accounts (it has no credit limit).
* ``ACCOUNTS_REDEMPTIONS_NAME`` - The name of the 'sales' account which is the
  recipient of any funds used to pay for orders
* ``ACCOUNTS_LAPSED_NAME`` - The name of the 'expired' account which is the
  recipient of any funds left if accounts that expire.  A cronjob is used to
  close expired accounts.

Running syncdb will create the appropriate tables and create accounts for based
on the above 3 settings.

If running with Oscar, add an additional path to your ``TEMPLATE_DIRS``::

    from accounts import TEMPLATE_DIR as ACCOUNTS_TEMPLATE_DIR

    TEMPLATE_DIRS = (
        ...
        ACCOUNTS_TEMPLATE_DIR)

You should also set-up a cronjob that calls::

    ./manage.py close_expired_accounts

to close any expired accounts and transfer their funds to the 'expired'
account.

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

* ``ACCOUNTS_SOURCE_NAME`` The name of the 'source' account
* ``ACCOUNTS_SALES_NAME`` The name of the 'sales' account
* ``ACCOUNTS_EXPIRED_NAME`` The name of the 'expired' account
* ``ACCOUNTS_MIN_INITIAL_VALUE`` The minimum value that can be used to create an
  account (or for a top-up)
* ``ACCOUNTS_MAX_INITIAL_VALUE`` The maximum value that can be transferred to an
  account.

Contributing
------------

Fork repo, set-up virtualenv and run::
    
    make install

Run tests with::
    
    ./runtests.py
