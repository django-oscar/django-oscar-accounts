import logging

from accounts import models
from accounts import exceptions

logger = logging.getLogger('accounts')


def transfer(source, destination, amount, user=None, description=None):
    """
    Transfer funds between source and destination accounts.

    Will raise a accounts.exceptions.AccountException if anything goes wrong.

    :source: Account to debit
    :destination: Account to credit
    :amount: Amount to transfer
    :user: Authorising user
    :description: Description of transaction
    """
    msg = "Transfer of %.2f from account #%d to account #%d"
    if user:
        msg += " authorised by user #%d (%s)" % (user.id, user.username,)
    if description:
        msg += " '%s'" % description
    try:
        transfer = models.Transfer.objects.create(
            source, destination, amount, user, description)
    except exceptions.AccountException, e:
        logger.warning("%s - failed: '%s'", msg, e)
        raise
    except Exception, e:
        logger.error("%s - failed: '%s'", msg, e)
        raise exceptions.AccountException(
            "Unable to complete transfer: %s" % e)
    else:
        logger.info("%s - successful, transfer: %s", msg,
                    transfer.reference)
        return transfer


def reverse(transfer, user=None, description=None):
    """
    Reverse a previous transfer, returning the money to the original source.
    """
    msg = "Reverse of transfer #%d" % transfer.id
    if user:
        msg += " authorised by user #%d (%s)" % (user.id, user.username,)
    if description:
        msg += " '%s'" % description
    try:
        transfer = models.Transfer.objects.create(
            source=transfer.destination,
            destination=transfer.source,
            amount=transfer.amount, user=user, description=description)
    except exceptions.AccountException, e:
        logger.warning("%s - failed: '%s'", msg, e)
        raise
    except Exception, e:
        logger.error("%s - failed: '%s'", msg, e)
        raise exceptions.AccountException(
            "Unable to reverse transfer: %s" % e)
    else:
        logger.info("%s - successful, transfer: %s", msg,
                    transfer.reference)
        return transfer
