import logging

from django.db import transaction
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _
from oscar.apps.payment.exceptions import UnableToTakePayment

from accounts import facade, exceptions, core, codes

Account = get_model('accounts', 'Account')
Transfer = get_model('accounts', 'Transfer')

logger = logging.getLogger('accounts')


def user_accounts(user):
    """
    Return accounts available to the passed user
    """
    return Account.active.filter(primary_user=user)


def _get_and_verify_transfers(order_number, user, allocations):
    """
    Check if the allocations are still valid; the accounts may have changed
    status since the allocations were written to the session.

    Will raise UnableToTakePayment if any of the transfers is invalid.
    """
    transfers = []
    destination = core.redemptions_account()
    for code, amount in allocations.items():
        try:
            account = Account.active.get(code=code)
        except Account.DoesNotExist:
            logger.warning("Verification failed for transfer of %s from "
                           "unknown account (%s) for order #%s",
                           amount, account.code, order_number)
            raise UnableToTakePayment(
                _("No active account found with code %s") % code)

        # We verify each transaction
        try:
            Transfer.objects.verify_transfer(
                account, destination, amount, user)
        except exceptions.AccountException, e:
            logger.warning("Verification failed for transfer of %s from '%s' "
                           "(%s) for order #%s",
                           amount, account.name, account.code, order_number)
            raise UnableToTakePayment(str(e))

        transfers.append((account, destination, amount))

        logger.info("Verified transfer of %s from '%s' (%s) for order #%s",
                    amount, account.name, account.code, order_number)

    logger.info("Verified order's #%s transfers", order_number)

    return transfers


def can_redeem(order_number, user, allocations):
    """
    Check if the allocations can be redeemed. App might want to check if it is
    so, run custom business logic and afterwards do actual redemption.
    """
    try:
        _get_and_verify_transfers(order_number, user, allocations)
    except UnableToTakePayment:
        return False
    else:
        return True


def redeem(order_number, user, allocations):
    """
    Settle payment for the passed set of account allocations.

    An error will be raised in case that any transaction can't got through.
    """
    # First, we need to check if the allocations are still valid
    transfers = _get_and_verify_transfers(order_number, user, allocations)
    # All transfers verified, now redeem atomicaly
    redeem_transaction = transaction.savepoint()
    try:
        for account, destination, amount in transfers:
            facade.transfer(
                account, destination, amount, user=user,
                merchant_reference=order_number,
                description="Redeemed to pay for order %s" % order_number)
        transaction.savepoint_commit(redeem_transaction)
    except Exception, exception:
        logger.error("Rollbacking transaction because exception: '%s'",
                     unicode(exception))
        transaction.savepoint_rollback(redeem_transaction)
        raise exception


def create_giftcard(order_number, user, amount):
    source = core.paid_source_account()
    code = codes.generate()
    destination = Account.objects.create(
        code=code
    )
    facade.transfer(source, destination, amount, user,
                    "Create new account")
