import logging

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


def redeem(order_number, user, allocations):
    """
    Settle payment for the passed set of account allocations.

    An error will be raised in case that any transaction can't got through.
    """
    # First, we need to check if the allocations are still valid
    transfers = get_and_verify_transfers(order_number, user, allocations)
    # All transfers verified, now redeem
    redeemed_transfers = redeem_verified_transfers(order_number, user, transfers)

def get_and_verify_transfers(order_number, user, allocations):
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
            logger.info("Verification failed for transfer of %s from unknown "
                        "account (%s) for order #%s",
                        amount, account.code, order_number)
            raise UnableToTakePayment(
                _("No active account found with code %s") % code)

        # We verify each transaction
        try:
            Transfer.objects.verify_transfer(
                account, destination, amount, user)
        except exceptions.AccountException, e:
            logger.info("Verification failed for transfer of %s from '%s' (%s) "
                        "for order #%s",
                        amount, account.name, account.code, order_number)
            raise UnableToTakePayment(str(e))

        transfers.append((account, destination, amount))

        logger.info("Verified transfer of %s from '%s' (%s) for order #%s",
            amount, account.name, account.code, order_number)

    logger.info("Verified order's #%s transfers", order_number)

    return transfers

def redeem_verified_transfers(order_number, user, transfers):
    """
    Try to redeem a list of transfers, and on failure try to reverse them. In any
    case, fail if not everything goes as planned.

    Returns a list of redeemd transfers, which can be used to reverse them.
    """
    redeemed_transfers = []
    for account, destination, amount in transfers:
        try:
            transfer = facade.transfer(account, destination, amount, user=user,
                merchant_reference=order_number,
                description="Redeemed to pay for order %s" % order_number)
            redeemed_transfers.append(transfer)
        except Exception, redeem_exception:
            # Reverse redeemed transfers
            if redeemed_transfers:
                try:
                    refund_redeemed_transfers(user, redeemed_transfers)
                except:
                    # We couldn't reverse all of them, fail
                    logger.error("Reediming from account '%s' (%s) for order "
                        "#%s failed, refunding redeemed transfers failed\n"
                        "Redeem exception:\n%s\n",
                        account.name, account.code, order_number,
                        unicode(redeem_exception))
                else:
                    # Reversal was successful
                    logger.warning("Reediming from account '%s' (%s) for order "
                        "#%s failed, successfuly refunded redeemed transfers\n"
                        "Redeem exception:\n%s\n",
                        account.name, account.code, order_number,
                        unicode(redeem_exception))

            # Fail anyway
            raise UnableToTakePayment(
                _(unicode(redeem_exception)))
        else:
            logging.info("Transfer from account '%s' (%s) for order #%s went through",
                account.name, account.code, order_number)

    return redeemed_transfers

def reverse_redeemed_transfers(redeemed_transfers):
    """
    Try to reverse as many redeemed transfers as possible, and raise the first
    exception caught
    """
    reversal_exception = None
    for transfer in redeemed_transfers:
        # Try to reverse as many transfers as possible
        try:
            facade.reverse(transfer)
        except Exception, e:
            # A relevant message will be logged if the reversal fails
            reversal_exception = e

    # Fail if any reversal failed
    if reversal_exception:
        raise reversal_exception


def create_giftcard(order_number, user, amount):
    source = core.paid_source_account()
    code = codes.generate()
    destination = Account.objects.create(
        code=code
    )
    facade.transfer(source, destination, amount, user,
                    "Create new account")
