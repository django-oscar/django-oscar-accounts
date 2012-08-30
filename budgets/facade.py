from django.db import transaction

from budgets import models


def transfer(source, destination, amount, user, description=None):
    """
    Transfer funds between source budget and destination budget

    :source: Budget to debit
    :destination: Budget to credit
    :amount: Amount to transfer
    :user: Authorising user
    """
    with transaction.commit_on_success():
        txn = models.Transaction.objects.create(
            source, destination, amount, user, description)
        return txn
