import hashlib
import hmac
from decimal import Decimal as D

from django.conf import settings
from django.db import models, transaction
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from oscar.core.compat import AUTH_USER_MODEL
from treebeard.mp_tree import MP_Node

from oscar_accounts import exceptions


class ActiveAccountManager(models.Manager):

    def get_queryset(self):
        now = timezone.now()
        qs = super().get_queryset()
        return qs.filter(
            models.Q(start_date__lte=now) | models.Q(start_date=None)).filter(
                models.Q(end_date__gte=now) | models.Q(end_date=None)
        )


class ExpiredAccountManager(models.Manager):

    def get_queryset(self):
        now = timezone.now()
        qs = super().get_queryset()
        return qs.filter(end_date__lt=now)


class AccountType(MP_Node):
    code = models.CharField(max_length=128, unique=True, null=True, blank=True)
    name = models.CharField(max_length=128)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    @property
    def full_name(self):
        names = [a.name for a in self.get_ancestors()]
        names.append(self.name)
        return " / ".join(names)


class Account(models.Model):
    # Metadata
    name = models.CharField(
        max_length=128, unique=True, null=True, blank=True)
    description = models.TextField(
        null=True, blank=True, help_text=_(
            "This text is shown to customers during checkout"))
    account_type = models.ForeignKey(
        'AccountType', models.CASCADE, related_name='accounts', null=True)

    # Some accounts are not linked to a specific user but are activated by
    # entering a code at checkout.
    code = models.CharField(
        max_length=128, unique=True, null=True, blank=True)

    # Each account can have multiple users who can use it for transactions.  In
    # most cases, there will only be one user and so we use a 'primary'
    # user FK for this scenario for simplicitiy.
    #
    # In other circumstances, there will be a group of users who can access the
    # account - and so we use 'secondary' users for this purpose.
    #
    # As a rule of thumb, you don't normally need to use both primary_user and
    # secondary_users within the same project - just one or the other.
    primary_user = models.ForeignKey(
        AUTH_USER_MODEL, models.SET_NULL, related_name="accounts",
        null=True, blank=True
    )
    secondary_users = models.ManyToManyField(AUTH_USER_MODEL, blank=True)

    # Track the status of a account - this is often used so that expired
    # account can have their money transferred back to some parent account and
    # then be closed.
    OPEN, FROZEN, CLOSED = 'Open', 'Frozen', 'Closed'
    status = models.CharField(max_length=32, default=OPEN)

    # This is the limit to which the account can go into debt.  The default is
    # zero which means the account cannot run a negative balance.  A 'source'
    # account will have no credit limit meaning it can transfer funds to other
    # accounts without limit.
    credit_limit = models.DecimalField(decimal_places=2, max_digits=12,
                                       default=D('0.00'), null=True,
                                       blank=True)

    # For performance, we keep a cached balance.  This can always be
    # recalculated from the account transactions.
    balance = models.DecimalField(decimal_places=2, max_digits=12,
                                  default=D('0.00'), null=True)

    # Accounts can have an date range to indicate when they are 'active'.  Note
    # that these dates are ignored when creating a transfer.  It is up to your
    # client code to use them to enforce business logic.
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    # Accounts are sometimes restricted to only work on a specific range of
    # products.  This is the only link with Oscar.
    product_range = models.ForeignKey('offer.Range', models.CASCADE, null=True, blank=True)

    # Allow accounts to be restricted for products only (ie can't be used to
    # pay for shipping)
    can_be_used_for_non_products = models.BooleanField(
        default=True,
        help_text=("Whether this account can be used to pay for "
                   "shipping and other charges"))

    date_created = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    active = ActiveAccountManager()
    expired = ExpiredAccountManager()

    class Meta:
        abstract = True

    def __str__(self):
        if self.code:
            return self.code
        if self.name:
            return self.name
        return 'Anonymous'

    def is_active(self):
        if self.start_date is None and self.end_date is None:
            return True
        now = timezone.now()
        if self.start_date and self.end_date is None:
            return now >= self.start_date
        if self.start_date is None and self.end_date:
            return now < self.end_date
        return self.start_date <= now < self.end_date

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.upper()
        # Ensure the balance is always correct when saving
        self.balance = self._balance()
        return super().save(*args, **kwargs)

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
        """
        Test if the a debit for the passed amount is permitted
        """
        if self.amount_available is None:
            return True
        return amount <= self.amount_available

    @property
    def amount_available(self):
        if self.credit_limit is None:
            return None
        return self.balance + self.credit_limit

    def permitted_allocation(self, basket, shipping_total, order_total):
        """
        Return max permitted allocation from this account to pay for the passed
        basket

        :basket: The basket being paid for
        :shipping_total: The cost of shipping
        :order_total: The order total (which includes the shipping total)
        """
        if not self.can_be_used_for_non_products:
            total = order_total - shipping_total
        else:
            total = order_total
        if not self.product_range:
            return min(total, self.balance)
        range_total = D('0.00')
        for line in basket.all_lines():
            if self.product_range.contains_product(line.product):
                range_total += line.line_price_incl_tax_and_discounts
        if self.can_be_used_for_non_products:
            range_total += shipping_total
        return min(range_total, self.balance)

    def is_open(self):
        return self.status == self.__class__.OPEN

    def is_closed(self):
        return self.status == self.__class__.CLOSED

    def is_frozen(self):
        return self.status == self.__class__.FROZEN

    @property
    def is_editable(self):
        """
        Test whether this account can be edited within the dashboard
        """
        return self.code is not None

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

    def days_remaining(self, from_date=None):
        if self.end_date is None:
            return None
        if from_date is None:
            from_date = timezone.now()
        if from_date > self.end_date:
            return 0
        return (self.end_date - from_date).days

    def close(self):
        # Only account with zero balance can be closed
        # Saves these changes to the database but doesn't save any other changes you may have made to the object.
        if self.balance > 0:
            raise exceptions.AccountNotEmpty()
        self.status = self.__class__.CLOSED
        self.save(update_fields=['status'])

    def as_dict(self):
        data = {
            'code': self.code,
            'start_date': '',
            'end_date': '',
            'status': self.status,
            'balance': "%.2f" % self.balance,
            'redemptions_url': reverse('oscar_accounts_api:account-redemptions',
                                       kwargs={'code': self.code}),
            'refunds_url': reverse('oscar_accounts_api:account-refunds',
                                   kwargs={'code': self.code})}

        if self.start_date:
            data['start_date'] = self.start_date.isoformat()
        if self.end_date:
            data['end_date'] = self.end_date.isoformat()
        return data


class PostingManager(models.Manager):
    """
    Custom manager to provide a new 'create' method to create a new transfer.

    Apparently, finance people refer to "posting a transaction"; hence why this
    """

    def create(self, source, destination, amount, parent=None,
               user=None, merchant_reference=None, description=None):
        # Write out transfer (which involves multiple writes).  We use a
        # database transaction to ensure that all get written out correctly.
        self.verify_transfer(source, destination, amount, user)
        with transaction.atomic():
            transfer = self.get_queryset().create(
                source=source,
                destination=destination,
                amount=amount,
                parent=parent,
                user=user,
                merchant_reference=merchant_reference,
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
    # We generate a reference for each transaction to avoid passing around
    # primary keys
    reference = models.CharField(max_length=64, unique=True, null=True)

    source = models.ForeignKey('oscar_accounts.Account', models.CASCADE,
                               related_name='source_transfers')
    destination = models.ForeignKey('oscar_accounts.Account', models.CASCADE,
                                    related_name='destination_transfers')
    amount = models.DecimalField(decimal_places=2, max_digits=12)

    # We keep track of related transfers (eg multiple refunds of the same
    # redemption) using a parent system
    parent = models.ForeignKey('self', models.CASCADE, null=True,
                               related_name='related_transfers')

    # Optional meta-data about transfer
    merchant_reference = models.CharField(max_length=128, null=True)
    description = models.CharField(max_length=256, null=True)

    # We record who the user was who authorised this transaction.  As
    # transactions should never be deleted, we allow this field to be null and
    # also record some audit information.
    user = models.ForeignKey(AUTH_USER_MODEL, models.SET_NULL, related_name="transfers", null=True)
    username = models.CharField(max_length=150)

    date_created = models.DateTimeField(auto_now_add=True)

    # Use a custom manager that extends the create method to also create the
    # account transactions.
    objects = PostingManager()

    def __str__(self):
        return self.reference

    class Meta:
        abstract = True
        ordering = ('-date_created',)

    def delete(self, *args, **kwargs):
        raise RuntimeError("Transfers cannot be deleted")

    def save(self, *args, **kwargs):
        # Store audit information about authorising user (if one is set)
        if self.user:
            self.username = self.user.get_username()
        # We generate a transaction reference using the PK of the transfer so
        # we save the transfer first
        super().save(*args, **kwargs)
        if not self.reference:
            self.reference = self._generate_reference()
            super().save(update_fields=['reference'])

    def _generate_reference(self):
        obj = hmac.new(key=settings.SECRET_KEY.encode(),
                       msg=str(self.id).encode(),
                       digestmod=hashlib.md5)
        return obj.hexdigest().upper()

    @property
    def authorisor_username(self):
        if self.user:
            return self.user.get_username()
        return self.username

    def max_refund(self):
        """
        Return the maximum amount that can be refunded against this transfer
        """
        aggregates = self.related_transfers.filter(
            source=self.destination).aggregate(sum=Sum('amount'))
        already_refunded = aggregates['sum']
        if already_refunded is None:
            return self.amount
        return self.amount - already_refunded

    def as_dict(self):
        return {
            'reference': self.reference,
            'source_code': self.source.code,
            'source_name': self.source.name,
            'destination_code': self.destination.code,
            'destination_name': self.destination.name,
            'amount': "%.2f" % self.amount,
            'available_to_refund': "%.2f" % self.max_refund(),
            'datetime': self.date_created.isoformat(),
            'merchant_reference': self.merchant_reference,
            'description': self.description,
            'reverse_url': reverse(
                'oscar_accounts_api:transfer-reverse',
                kwargs={'reference': self.reference}),
            'refunds_url': reverse(
                'oscar_accounts_api:transfer-refunds',
                kwargs={'reference': self.reference})}


class Transaction(models.Model):
    # Every transfer of money should create two rows in this table.
    # (a) the debit from the source account
    # (b) the credit to the destination account
    transfer = models.ForeignKey('oscar_accounts.Transfer', models.CASCADE,
                                 related_name="transactions")
    account = models.ForeignKey('oscar_accounts.Account', models.CASCADE,
                                related_name='transactions')

    # The sum of this field over the whole table should always be 0.
    # Credits should be positive while debits should be negative
    amount = models.DecimalField(decimal_places=2, max_digits=12)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return u"Ref: %s, amount: %.2f" % (
            self.transfer.reference, self.amount)

    class Meta:
        unique_together = ('transfer', 'account')
        abstract = True

    def delete(self, *args, **kwargs):
        raise RuntimeError("Transactions cannot be deleted")


class IPAddressRecord(models.Model):
    ip_address = models.GenericIPAddressField(_("IP address"), unique=True)
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

    def __str__(self):
        return self.ip_address

    def increment_failures(self):
        self.total_failures += 1
        self.consecutive_failures += 1
        self.date_last_failure = timezone.now()
        self.save(update_fields=['total_failures', 'consecutive_failures', 'date_last_failure'])

    def increment_blocks(self):
        self.total_blocks += 1
        self.save(update_fields=['total_blocks'])

    def reset(self):
        self.consecutive_failures = 0
        self.save(update_fields=['consecutive_failures'])

    def is_blocked(self):
        return (self.is_temporarily_blocked() or self.is_permanently_blocked())

    def is_temporarily_blocked(self):
        if self.consecutive_failures < self.FREEZE_THRESHOLD:
            return False

        # If you've had several consecutive failures, we impose a miniumum
        # period between each allowed request.
        now = timezone.now()
        time_since_last_failure = now - self.date_last_failure
        return time_since_last_failure.seconds < self.COOLING_OFF_PERIOD

    def is_permanently_blocked(self):
        return self.total_failures > self.BLOCK_THRESHOLD
