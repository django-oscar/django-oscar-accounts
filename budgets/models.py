from decimal import Decimal as D
import datetime

from django.db import models
from django.db.models import Sum

from budgets import exceptions


class Budget(models.Model):
    name = models.CharField(max_length=128, unique=True, null=True)

    # Some budgets are not linked to a specific user but are activated by
    # entering a code at checkout.
    code = models.CharField(max_length=128, unique=True, null=True)

    # This is the limit to which the budget can do into debt.  The default is
    # zero which means the budget cannot run a negative balance.
    credit_limit = models.DecimalField(decimal_places=2, max_digits=12,
                                       default=D('0.00'), null=True)

    # Budgets can have an date range when they can be used.
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)

    # Each budget can have multiple users who can use it for transactions.  In
    # many cases, there will only be one user though and so we use a 'primary'
    # user for this scenario.
    primary_user = models.ForeignKey('auth.User', related_name="budgets",
                                     null=True)
    secondary_users = models.ManyToManyField('auth.User')

    date_created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        name = self.name if self.name else "Anonymous budget"
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

    def balance(self):
        aggregates = self.transactions.aggregate(sum=Sum('amount'))
        sum = aggregates['sum']
        return D('0.00') if sum is None else sum

    def is_debit_permitted(self, amount):
        if self.credit_limit is None:
            return True
        available = self.balance() + self.credit_limit
        return amount <= available


class TransactionManager(models.Manager):

    def create(self, source, destination, amount, user, description=None):
        """
        Create a new transaction
        """
        self.verify_transaction(source, destination, amount)
        txn = self.get_query_set().create(user=user, description=description)
        txn.budget_transactions.create(
            budget=source, amount=-amount)
        txn.budget_transactions.create(
            budget=destination, amount=amount)
        return txn

    def verify_transaction(self, source, destination, amount):
        """
        Test whether the proporsed transaction is permitted.
        """
        if amount <= 0:
            raise exceptions.InvalidAmount("Debits must use a positive amount")
        if not source.is_active():
            raise exceptions.InactiveBudget("Source budget is inactive")
        if not destination.is_active():
            raise exceptions.InactiveBudget("Destination budget is inactive")
        if not source.is_debit_permitted(amount):
            msg = "Unable to debit %.2f from budget #%d:"
            raise exceptions.InsufficientBudget(
                msg % (amount, source.id))


class Transaction(models.Model):
    """
    A transaction.

    Each transaction links to TWO budget transactions
    """
    # Optional description of what this transaction was
    description = models.CharField(max_length=256, null=True)

    # We record who the user was who authorised this transaction.  As
    # transactions should never be deleted, we allow this field to be null and
    # also record some audit information.
    user = models.ForeignKey('auth.User', related_name="budget_transactions",
                             null=True, on_delete=models.SET_NULL)

    date_created = models.DateTimeField(auto_now_add=True)

    # Use a custom manager that extends the create method to also create the
    # budget transactions.
    objects = TransactionManager()


class BudgetTransaction(models.Model):
    # Each transfer creates two transaction instances.  They should both have
    # the same txn ID.
    transaction = models.ForeignKey(Transaction,
                                    related_name="budget_transactions")

    # Every transfer of money should create two rows in this table.
    # (a) the debit from the source budget
    # (b) the credit to the destination budget
    budget = models.ForeignKey(Budget, related_name='transactions')

    # The sum of this field over the whole table should always be 0
    # Credits should be positive while debits should be negative
    amount = models.DecimalField(decimal_places=2, max_digits=12)

    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('transaction', 'budget')
