import logging

from budgets import models
from budgets import exceptions

logger = logging.getLogger('budgets')


def transfer(source, destination, amount, user, description=None):
    """
    Transfer funds between source budget and destination budget.

    Will raise a budget.exceptions.BudgetException if anything goes wrong.

    :source: Budget to debit
    :destination: Budget to credit
    :amount: Amount to transfer
    :user: Authorising user
    :description: Description of transaction
    """
    msg = "Transfer of %.2f from budget #%d to budget #%d"
    if user:
        msg += " authorised by user #%d (%s)" % (user.id, user.username,)
    if description:
        msg += " '%s'" % description
    try:
        txn = models.Transaction.objects.create(
            source, destination, amount, user, description)
    except exceptions.BudgetException, e:
        logger.warning("%s - failed: '%s'", msg, e)
        raise
    except Exception, e:
        logger.error("%s - failed: '%s'", msg, e)
        raise exceptions.BudgetException("Unable to complete transfer: %s" % e)
    else:
        logger.info("%s - successful, transaction: %s", msg, txn.reference)
        return txn
