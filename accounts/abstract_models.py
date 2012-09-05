from decimal import Decimal as D
import datetime

from django.db import models
from django.db import transaction
from django.db.models import Sum

from accounts import exceptions


class ExpiredAccountManager(models.Manager):

    def get_query_set(self):
        today = datetime.date.today()
        qs = super(ExpiredAccountManager, self).get_query_set()
        return qs.filter(end_date__lte=today)


class Account(models.Model):
    name = models.CharField(max_length=128, unique=True, null=True,
                            blank=True)

    # Some accounts will be categorised
    category = models.CharField(max_length=256, null=True)

    # Some account are not linked to a specific user but are activated by
    # entering a code at checkout.
    code = models.CharField(max_length=128, unique=True, null=True,
                            blank=True)

    # Track the status of a account - this is often used so that expired account
    # can have their money transferred back to some parent account and then be
    # closed.
    OPEN, CLOSED = 'Open', 'Closed'
    status = models.CharField(max_length=32, default=OPEN)

    # This is the limit to which the account can do into debt.  The default is
    # zero which means the account cannot run a negative balance.
    credit_limit = models.DecimalField(decimal_places=2, max_digits=12,
                                       default=D('0.00'), null=True)

    # For performance reasons, we keep a cached balance
    balance = models.DecimalField(decimal_places=2, max_digits=12,
                                  default=D('0.00'), null=True)

    # Accounts can have an date range when they can be used as a source.  You
    # can still transfer into accounts when they are not active.
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # Each account can have multiple users who can use it for transactions.  In
    # many cases, there will only be one user though and so we use a 'primary'
    # user for this scenario.
    primary_user = models.ForeignKey('auth.User', related_name="accounts",
                                     null=True, blank=True)
    secondary_users = models.ManyToManyField('auth.User', blank=True)

    date_created = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    expired = ExpiredAccountManager()

    class Meta:
        abstract = True

    def __unicode__(self):
        name = self.name if self.name else "Anonymous account"
        if self.credit_limit is not None:
            name += " (credit limit: %.2f)" % self.credit_limit
        else:
            name += " (unlimited credit)"
        return name

    def is_active(self):
        if self.start_date is None and self.end_date is None:
            return True
        today = datetime.date.today()
        if self.start_date and self.end_date is None:
            return today >= self.start_date
        if self.start_date is None and self.end_date:
            return today < self.end_date
        return self.start_date <= today < self.end_date

    def update_balance(self):
        self.balance = self._balance()
        self.save()

    def _balance(self):
        aggregates = self.transactions.aggregate(sum=Sum('amount'))
        sum = aggregates['sum']
        return D('0.00') if sum is None else sum

    def num_transactions(self):
        return self.transactions.all().count()

    def is_debit_permitted(self, amount):
        if self.credit_limit is None:
            return True
        available = self.balance + self.credit_limit
        return amount <= available

    def is_open(self):
        return self.status == self.__class__.OPEN

    def close(self):
        # Only account with zero balance can be closed
        if self.balance > 0:
            raise exceptions.AccountNotEmpty()
        self.status = self.__class__.CLOSED
        self.save()


class PostingManager(models.Manager):
    """
    Custom manager to provide a new 'create' method to create a new transfer.

    Apparently, finance people refer to "posting a transaction"; hence why this
    """

    def create(self, source, destination, amount, user=None, description=None):
        # Write out transfer (which involves multiple writes).  We use a
        # database transaction to ensure that all get written out correctly.
        self.verify_transfer(source, destination, amount)
        with transaction.commit_on_success():
            transfer = self.get_query_set().create(user=user,
                                                   description=description)
            # Create transaction records for audit trail
            transfer.transactions.create(
                account=source, amount=-amount)
            transfer.transactions.create(
                account=destination, amount=amount)
            # Update the cached balances on the accounts
            source.update_balance()
            destination.update_balance()
            return self._wrap(transfer)

    def _wrap(self, obj):
        # Dumb method that is here only so that it can be mocked to test the
        # transaction behaviour.
        return obj

    def verify_transfer(self, source, destination, amount):
        """
        Test whether the proposed transaction is permitted.  Raise an exception
        if it is not.
        """
        if amount <= 0:
            raise exceptions.InvalidAmount("Debits must use a positive amount")
        if not source.is_active():
            raise exceptions.InactiveAccount("Source account is inactive")
        if not source.is_open():
            raise exceptions.ClosedAccount("Source account has been closed")
        if not destination.is_open():
            raise exceptions.ClosedAccount(
                "Destination account has been closed")
        if not source.is_debit_permitted(amount):
            msg = "Unable to debit %.2f from account #%d:"
            raise exceptions.InsufficientFunds(
                msg % (amount, source.id))


class Transfer(models.Model):
    """
    A transfer of funds between two accounts.

    This object records the meta-data about the transfer such as a reference
    number for it and who was the authorisor.  The financial details are help
    within the transactions.  Each transfer links to TWO account transactions
    """
    # Optional description of what this transfer was
    description = models.CharField(max_length=256, null=True)

    # We record who the user was who authorised this transaction.  As
    # transactions should never be deleted, we allow this field to be null and
    # also record some audit information.
    user = models.ForeignKey('auth.User', related_name="transfers",
                             null=True, on_delete=models.SET_NULL)
    username = models.CharField(max_length=128)

    date_created = models.DateTimeField(auto_now_add=True)

    # Use a custom manager that extends the create method to also create the
    # account transactions.
    objects = PostingManager()

    @property
    def reference(self):
        return "%08d" % self.id

    def __unicode__(self):
        return self.reference

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        raise RuntimeError("Transfers cannot be deleted")

    def save(self, *args, **kwargs):
        # Store audit information about authorising user (if one is set)
        if self.user:
            self.username = self.user.username
        return super(Transfer, self).save(*args, **kwargs)

    @property
    def authorisor_username(self):
        if self.user:
            return self.user.username
        return self.username


class Transaction(models.Model):
    # Every transfer of money should create two rows in this table.
    # (a) the debit from the source account
    # (b) the credit to the destination account
    transfer = models.ForeignKey('accounts.Transfer',
                               related_name="transactions")
    account = models.ForeignKey('accounts.Account', related_name='transactions')

    # The sum of this field over the whole table should always be 0.
    # Credits should be positive while debits should be negative
    amount = models.DecimalField(decimal_places=2, max_digits=12)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('transfer', 'account')
        abstract = True

    def delete(self, *args, **kwargs):
        raise RuntimeError("Transactions cannot be deleted")
