Managed accounts for Django
===========================

A 'managed account' is an allocation of money that can be debited and credited.  This 
package provides managed account functionality for use with the e-commerce framework 
[Oscar](https://github.com/tangentlabs/django-oscar).  It can also be used
standalone without Oscar.

Accounts can be used to implement a variety of interesting components, including:

* Giftcards
* Web accounts
* Loyalty schemes

Basically anything that involves tracking the movement of funds within a closed
system.

This package uses [double-entry bookkeeping](http://en.wikipedia.org/wiki/Double-entry_bookkeeping_system)
where every transaction is recorded twice (once for the source and once for the
destination).  This ensures the books always balance and there is full audit
trail of all transactional activity.  

If your project manages money, you should be using a library like this.  Your
finance people will thank you.

[![Build Status](https://travis-ci.org/tangentlabs/django-oscar-accounts.png)](https://travis-ci.org/tangentlabs/django-oscar-accounts)
[![Coverage Status](https://coveralls.io/repos/tangentlabs/django-oscar-accounts/badge.png?branch=master)](https://coveralls.io/r/tangentlabs/django-oscar-accounts)
[![Latest Version](https://pypip.in/v/django-oscar-accounts/badge.png)](https://crate.io/packages/django-oscar-accounts/)
[![Number of Downloads](https://pypip.in/d/django-oscar-accounts/badge.png)](https://crate.io/packages/django-oscar-accounts/)

Features
--------

* An account has a credit limit which defaults to zero.  Accounts can be set up
  with no credit limit so that they are a 'source' of money within the system.
  At least one account must be set up without a credit limit in order for money
  to move around the system.

* Accounts can have:
  - No users assigned
  - A single "primary" user - this is the most common case
  - A set of users assigned

* A user can have multiple accounts

* An account can have a start and end date to allow its usage in a limited time
  window

* An account can be restricted so that it can only be used to pay for a range of
  products.

* Accounts can be categorised

Screenshots
-----------

[![Dashboard account list](https://github.com/tangentlabs/django-oscar-accounts/raw/master/screenshots/dashboard-list.thumb.png)](https://github.com/tangentlabs/django-oscar-accounts/raw/master/screenshots/dashboard-list.png)
[![Create new account ](https://github.com/tangentlabs/django-oscar-accounts/raw/master/screenshots/dashboard-form.thumb.png)](https://github.com/tangentlabs/django-oscar-accounts/raw/master/screenshots/dashboard-form.png)
[![Dashboard account list](https://github.com/tangentlabs/django-oscar-accounts/raw/master/screenshots/dashboard-transfers.thumb.png)](https://github.com/tangentlabs/django-oscar-accounts/raw/master/screenshots/dashboard-transfers.png)
[![Dashboard account list](https://github.com/tangentlabs/django-oscar-accounts/raw/master/screenshots/dashboard-report.thumb.png)](https://github.com/tangentlabs/django-oscar-accounts/raw/master/screenshots/dashboard-report.png)

Installation
------------

Install using pip:

```bash
	pip install django-oscar-accounts
```

and add `accounts` to `INSTALLED_APPS`.  Then, add the following
settings:

* `ACCOUNTS_SOURCE_NAME` - The name of the 'source' account which is used to
  transfer funds to other accounts (it has no credit limit).
* `ACCOUNTS_REDEMPTIONS_NAME` - The name of the 'sales' account which is the
  recipient of any funds used to pay for orders
* `ACCOUNTS_LAPSED_NAME` - The name of the 'expired' account which is the
  recipient of any funds left if accounts that expire.  A cronjob is used to
  close expired accounts.

Running `manage.py syncdb` will create the appropriate tables and initialise accounts based
on the above 3 settings.

If running with Oscar, add an additional path to your `TEMPLATE_DIRS`:
``` python
from accounts import TEMPLATE_DIR as ACCOUNTS_TEMPLATE_DIR

TEMPLATE_DIRS = (
	...
	ACCOUNTS_TEMPLATE_DIR)
```

This allows the templates to be customised by overriding blocks instead of
replacing the entire template.

You should also set-up a cronjob that calls:

    ./manage.py close_expired_accounts

to close any expired accounts and transfer their funds to the 'expired'
account.

API
---

Create account instances using the manager:

``` python

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
```

Transfer funds using the facade:

``` python

from accounts import facade

staff_member = User.objects.get(username="staff")
trans = facade.transfer(source=no_credit_limit_account,
						destination=user_account,
						amount=Decimal('10.00'),
						user=staff_member)
```

Reverse transfers:

``` python
facade.reverse(trans, user=staff_member, 
				description="Just an example")
```

If the proposed transfer is invalid, an exception will be raised.  All
exceptions are subclasses of `accounts.exceptions.AccountException`.  Your
client code should look for exceptions of this type and handle them
appropriately.
 
Client code should only use the `accounts.models.Budget` class and the
two functions from `accounts.facade` - nothing else should be required.

Error handling
--------------

Note that the transfer operation is wrapped in its own database transaction to
ensure that only complete transfers are written out.  When using Django's
transaction middleware, you need to be careful.  If you have an unhandled
exception,  then account transfers will still be committed even though nothing
else will be.  To handle this, you need to make sure that, if an exception
occurs during your post-payment code, then you roll-back any transfers.

Here's a toy example:

``` python
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
```

In this situation, you'll end up with two transfers being created but no order.
While this isn't ideal, it's the best way of handling exceptions that occur
during order placement.

Multi-transfer payments
-----------------------

Projects will often allow users to have multiple accounts and pay for an order
using more than one.  This will involve several transfers and needs some careful handling
in your application code.

It normally makes sense to write your own wrapper around the accounts API to encapsulate
your business logic and error handling.  Here's an example:

``` python
from decimal import Decimal as D
from accounts import models, exceptions, facade


def redeem(order_number, user, amount):
    # Ensure there is a account for expenditure on orders
    destination = sales_account()
    
    # Get user's non-empty accounts ordered with the first to expire first
    accounts = models.Account.active.filter(
        user=user, balance__gt=0).order_by('end_date')

    # Build up a list of potential transfers
    transfers = []
    amount_to_allocate = D('0.00')
    for account in accounts:
        to_transfer = min(account.balance, amount_to_allocate)
        transfers.append((account, to_transfer))
        amount_to_allocate -= to_transfer
        if amount_to_allocate == D('0.00'):
            break

    # Check we have sufficient transfers to cover the requested amount
    if amount_to_allocate > D('0.00'):
        raise exceptions.InsufficientFunds()

    # Execute transfers to some 'Sales' account
    destination = models.Account.objects.get(name="Sales")
    completed_transfers = []
    try:
        for account, amount in transfers:
            transfer = facade.transfer(
                account, destination, amount, user=user,
                description="Order %s" % order_number)
            completed_transfers.append(transfer)
    except exceptions.AccountException, transfer_exc:
        # Something went wrong with one of the transfers (possibly a race condition).
        # We try and roll back all completed ones to get us back to a clean state.
        try:
            for transfer in completed_transfers:
                facade.reverse(transfer)
        except Exception, reverse_exc:
            # No man's land.  We're left with a partial redemption. This will
            # require an admin to intervene.
            logger.error("Order %s, transfers failed (%s) and reverse failed (%s)",
                         order_number, transfer_exc, reverse_exc)
            logger.exception(reverse_exc)

        # Raise an exception so that your client code can inform the user appropriately.
        raise RedemptionFailed()
    else:
        # All transfers completed ok
        return completed_transfers

As you can see, there is some careful handling of the scenario where not all transfers can be 
executed.

If you using Oscar then ensure that you create an `OrderSource` instance for every transfer (rather than
aggregating them all into one).  This will provide better audit information.  Here's some example code:

``` python

    try:
        transfers = api.redeem(order_number, user, total_incl_tax)
    except Exception:
        # Inform user of failed payment
    else:
        for transfer in transfers:
            source_type = SourceType.objects.get_or_create(name="Accounts")
            source = Source(
                source_type=source_type,
                amount_allocated=tranfer.amount,
                amount_debited=transfer.amount,
                reference=transfer.reference)
            self.add_payment_source(source)

Settings
--------

* `ACCOUNTS_SOURCE_NAME` The name of the 'source' account
* `ACCOUNTS_SALES_NAME` The name of the 'sales' account
* `ACCOUNTS_EXPIRED_NAME` The name of the 'expired' account
* `ACCOUNTS_MIN_INITIAL_VALUE` The minimum value that can be used to create an
  account (or for a top-up)
* `ACCOUNTS_MAX_INITIAL_VALUE` The maximum value that can be transferred to an
  account.

Contributing
------------

Fork repo, set-up virtualenv and run:

    make install

Run tests with:
    
    ./runtests.py
