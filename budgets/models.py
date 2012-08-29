from decimal import Decimal as D

from django.db import models


class Budget(models.Model):
    name = models.CharField(max_length=128, unique=True, null=True)

    # Some budgets are not linked to a specific user but are activated by
    # entering a code at checkout.
    code = models.CharField(max_length=128, unique=True, null=True)

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
    date_last_transation = models.DateTimeField(null=True)


class Transaction(models.Model):
    # Every transfer of money should create two rows in this table.
    # (a) the debit from the source budget
    # (b) the credit to the destination budget
    budget = models.ForeignKey(Budget)

    # The sum of this field over the whole table should always be 0
    # Credits should be positive while debits should be negative
    amount = models.DecimalField(decimal_places=2, max_digits=12,
                                       default=D('0.00'))

    date_created = models.DateTimeField(auto_now_add=True)