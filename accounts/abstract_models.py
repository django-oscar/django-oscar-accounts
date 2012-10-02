from decimal import Decimal as D
import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db import transaction
from django.db.models import Sum
from treebeard.mp_tree import MP_Node

from accounts import exceptions


class ActiveAccountManager(models.Manager):

    def get_query_set(self):
        today = datetime.date.today()
        qs = super(ActiveAccountManager, self).get_query_set()
        return qs.filter(
            models.Q(start_date__lte=today) |
            models.Q(start_date=None)).filter(
                models.Q(end_date__gte=today) |
                models.Q(end_date=None))


class ExpiredAccountManager(models.Manager):

    def get_query_set(self):
        today = datetime.date.today()
        qs = super(ExpiredAccountManager, self).get_query_set()
        return qs.filter(end_date__lt=today)


class AccountType(MP_Node):
    code = models.CharField(max_length=128, unique=True, null=True, blank=True)
    name = models.CharField(max_length=128)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name

    @property
    def full_name(self):
        names = [a.name for a in self.get_ancestors()]
        names.append(self.name)
        return " / ".join(names)


class Account(models.Model):
    # Metadata
    name = models.CharField(max_length=128, unique=True, null=True,
                            blank=True)
    description = models.TextField(
        null=True, blank=True, help_text=_(
            "This text is shown to customers during checkout"))
    account_type = models.ForeignKey('AccountType', related_name='accounts',
                                     null=True)

    # Some account are not linked to a specific user but are activated by
    # entering a code at checkout.
    code = models.CharField(max_length=128, unique=True, null=True,
                            blank=True)

    # Each account can have multiple users who can use it for transactions.  In
    # many cases, there will only be one user though and so we use a 'primary'
    # user for this scenario.
    primary_user = models.ForeignKey('auth.User', related_name="accounts",
                                     null=True, blank=True,
                                     on_delete=models.SET_NULL)
    secondary_users = models.ManyToManyField('auth.User', blank=True)

    # Track the status of a account - this is often used so that expired
    # account can have their money transferred back to some parent account and
    # then be closed.
    OPEN, FROZEN, CLOSED = 'Open', 'Frozen', 'Closed'
    status = models.CharField(max_length=32, default=OPEN)

    # This is the limit to which the account can do into debt.  The default is
    # zero which means the account cannot run a negative balance.
    credit_limit = models.DecimalField(decimal_places=2, max_digits=12,
                                       default=D('0.00'), null=True,
                                       blank=True)

    # For performance, we keep a cached balance
    balance = models.DecimalField(decimal_places=2, max_digits=12,
                                  default=D('0.00'), null=True)

    # Accounts can have an date range to indicate when they are 'active'.  Note
    # that these dates are ignored when creating a transfer.  It is up to your
    # client code to use them to enforce business logic.
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # Accounts are sometimes restricted to only work on a specific range of
    # products
    product_range = models.ForeignKey('offer.Range', null=True, blank=True)

    # Allow accounts to be restricted for products only (ie can't be used to
    # pay for shipping)
    can_be_used_for_non_products = models.BooleanField(default=True)

    date_created = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    active = ActiveAccountManager()
    expired = ExpiredAccountManager()

    class Meta:
        abstract = True

    def __unicode__(self):
        if self.name:
            return self.name
        if self.code:
            return _("Code account - %s") % self.code
        return _("Anonymous account")

    def is_active(self):
        if self.start_date is None and self.end_date is None:
            return True
        today = datetime.date.today()
        if self.start_date and self.end_date is None:
            return today >= self.start_date
        if self.start_date is None and self.end_date:
            return today < self.end_date
        return self.start_date <= today < self.end_date

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.upper()
        # Ensure the balance is always correct when saving
        self.balance = self._balance()
        return super(Account, self).save(*args, **kwargs)

    def _balance(self):
        aggregates = self.transactions.aggregate(sum=Sum('amount'))
        sum = aggregates['sum']
        return D('0.00') if sum is None else sum

    def num_transactions(self):
        return self.transactions.all().count()

    @property
    def has_credit_limit(self):
        return self.credit_limit is not None

    def is_debit_permitted(self, amount):
        if self.credit_limit is None:
            return True
        available = self.balance + self.credit_limit
        return amount <= available

    def permitted_allocation(self, basket, total):
        """
        Return max permitted allocation from this account to pay for the passed
        basket
        """
        if not self.product_range:
            return min(total, self.balance)
        range_total = D('0.00')
        for line in basket.all_lines():
            if self.product_range.contains_product(line.product):
                range_total += line.line_price_incl_tax_and_discounts
        return min(range_total, total, self.balance)

    def is_open(self):
        return self.status == self.__class__.OPEN

    def is_closed(self):
        return self.status == self.__class__.CLOSED

    def is_frozen(self):
        return self.status == self.__class__.FROZEN

    def can_be_authorised_by(self, user=None):
        """
        Test whether the passed user can authorise a transfer from this account
        """
        if user is None:
            return True
        if self.primary_user:
            return user == self.primary_user
        secondary_users = self.secondary_users.all()
        if secondary_users.count() > 0:
            return user in secondary_users
        return True

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
        self.verify_transfer(source, destination, amount, user)
        with transaction.commit_on_success():
            transfer = self.get_query_set().create(
                source=source,
                destination=destination,
                amount=amount,
                user=user,
                description=description)
            # Create transaction records for audit trail
            transfer.transactions.create(
                account=source, amount=-amount)
            transfer.transactions.create(
                account=destination, amount=amount)
            # Update the cached balances on the accounts
            source.save()
            destination.save()
            return self._wrap(transfer)

    def _wrap(self, obj):
        # Dumb method that is here only so that it can be mocked to test the
        # transaction behaviour.
        return obj

    def verify_transfer(self, source, destination, amount, user=None):
        """
        Test whether the proposed transaction is permitted.  Raise an exception
        if not.
        """
        if amount <= 0:
            raise exceptions.InvalidAmount("Debits must use a positive amount")
        if not source.is_open():
            raise exceptions.ClosedAccount("Source account has been closed")
        if not source.can_be_authorised_by(user):
            raise exceptions.AccountException(
                "This user is not authorised to make transfers from "
                "this account")
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
    source = models.ForeignKey('accounts.Account',
                               related_name='source_transfers')
    destination = models.ForeignKey('accounts.Account',
                                    related_name='destination_transfers')
    amount = models.DecimalField(decimal_places=2, max_digits=12)

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
        ordering = ('-date_created',)

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
    account = models.ForeignKey('accounts.Account',
                                related_name='transactions')

    # The sum of this field over the whole table should always be 0.
    # Credits should be positive while debits should be negative
    amount = models.DecimalField(decimal_places=2, max_digits=12)
    date_created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u"Ref: %s, amount: %.2f" % (
            self.transfer.reference, self.amount)

    class Meta:
        unique_together = ('transfer', 'account')
        abstract = True

    def delete(self, *args, **kwargs):
        raise RuntimeError("Transactions cannot be deleted")


class IPAddressRecord(models.Model):
    ip_address = models.IPAddressField(_("IP address"), unique=True)
    total_failures = models.PositiveIntegerField(default=0)
    consecutive_failures = models.PositiveIntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_last_failure = models.DateTimeField(null=True)

    # Above this threshold, you have to wait for the cooling off period
    # between attempts
    FREEZE_THRESHOLD = 3

    # Above this threshold, you are blocked indefinitely
    BLOCK_THRESHOLD = 10

    # Blocking period (in seconds)
    COOLING_OFF_PERIOD = 5 * 60

    class Meta:
        abstract = True
        verbose_name = _("IP address record")
        verbose_name_plural = _("IP address records")

    def increment_failures(self):
        self.total_failures += 1
        self.consecutive_failures += 1
        self.date_last_failure = datetime.datetime.now()
        self.save()

    def increment_blocks(self):
        self.total_blocks += 1
        self.save()

    def reset(self):
        self.consecutive_failures = 0
        self.save()

    def is_blocked(self):
        return (self.is_temporarily_blocked() or
                self.is_permanently_blocked())

    def is_temporarily_blocked(self):
        if self.consecutive_failures < self.FREEZE_THRESHOLD:
            return False

        # If you've had several consecutive failures, we impose a miniumum
        # period between each allowed request.
        now = datetime.datetime.now()
        time_since_last_failure = now - self.date_last_failure
        return time_since_last_failure.seconds < self.COOLING_OFF_PERIOD

    def is_permanently_blocked(self):
        return self.total_failures > self.BLOCK_THRESHOLD
