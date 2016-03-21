import logging

from oscar.core.loading import get_model

from oscar_accounts import core, exceptions

Account = get_model('oscar_accounts', 'Account')
Transfer = get_model('oscar_accounts', 'Transfer')

logger = logging.getLogger('oscar_accounts')


def close_expired_accounts():
    """
    Close expired, open accounts and transfer any remaining balance to an
    expiration account.
    """
    accounts = Account.expired.filter(
        status=Account.OPEN)
    logger.info("Found %d open accounts to close", accounts.count())
    destination = core.lapsed_account()
    for account in accounts:
        balance = account.balance
        try:
            transfer(account, destination,
                     balance, description="Closing account")
        except exceptions.AccountException as e:
            logger.error("Unable to close account #%d - %s", account.id, e)
        else:
            logger.info(("Account #%d successfully expired - %d transferred "
                         "to sales account"), account.id, balance)
            account.close()


def transfer(source, destination, amount,
             parent=None, user=None, merchant_reference=None,
             description=None):
    """
    Transfer funds between source and destination accounts.

    Will raise a accounts.exceptions.AccountException if anything goes wrong.

    :source: Account to debit
    :destination: Account to credit
    :amount: Amount to transfer
    :parent: Parent transfer to reference
    :user: Authorising user
    :merchant_reference: An optional merchant ref associated with this transfer
    :description: Description of transaction
    """
    if source.id == destination.id:
        raise exceptions.AccountException(
            "The source and destination accounts for a transfer "
            "must be different."
        )
    msg = "Transfer of %.2f from account #%d to account #%d" % (
        amount, source.id, destination.id)
    if user:
        msg += " authorised by user #%d (%s)" % (user.id, user.get_username())
    if description:
        msg += " '%s'" % description
    try:
        transfer = Transfer.objects.create(
            source, destination, amount, parent, user,
            merchant_reference, description)
    except exceptions.AccountException as e:
        logger.warning("%s - failed: '%s'", msg, e)
        raise
    except Exception as e:
        logger.error("%s - failed: '%s'", msg, e)
        raise exceptions.AccountException(
            "Unable to complete transfer: %s" % e)
    else:
        logger.info("%s - successful, transfer: %s", msg,
                    transfer.reference)
        return transfer


def reverse(transfer, user=None, merchant_reference=None, description=None):
    """
    Reverse a previous transfer, returning the money to the original source.
    """
    msg = "Reverse of transfer #%d" % transfer.id
    if user:
        msg += " authorised by user #%d (%s)" % (user.id, user.get_username())
    if description:
        msg += " '%s'" % description
    try:
        transfer = Transfer.objects.create(
            source=transfer.destination,
            destination=transfer.source,
            amount=transfer.amount, user=user,
            merchant_reference=merchant_reference,
            description=description)
    except exceptions.AccountException as e:
        logger.warning("%s - failed: '%s'", msg, e)
        raise
    except Exception as e:
        logger.error("%s - failed: '%s'", msg, e)
        raise exceptions.AccountException(
            "Unable to reverse transfer: %s" % e)
    else:
        logger.info("%s - successful, transfer: %s", msg,
                    transfer.reference)
        return transfer
