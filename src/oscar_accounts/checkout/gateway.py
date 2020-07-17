from django.utils.translation import gettext_lazy as _
from oscar.apps.payment.exceptions import UnableToTakePayment
from oscar.core.loading import get_model

from oscar_accounts import codes, core, exceptions, facade

Account = get_model('oscar_accounts', 'Account')
Transfer = get_model('oscar_accounts', 'Transfer')


def user_accounts(user):
    """
    Return accounts available to the passed user
    """
    return Account.active.filter(primary_user=user)


def redeem(order_number, user, allocations):
    """
    Settle payment for the passed set of account allocations

    Will raise UnableToTakePayment if any of the transfers is invalid
    """
    # First, we need to check if the allocations are still valid.  The accounts
    # may have changed status since the allocations were written to the
    # session.
    transfers = []
    destination = core.redemptions_account()
    for code, amount in allocations.items():
        try:
            account = Account.active.get(code=code)
        except Account.DoesNotExist:
            raise UnableToTakePayment(
                _("No active account found with code %s") % code)

        # We verify each transaction
        try:
            Transfer.objects.verify_transfer(
                account, destination, amount, user)
        except exceptions.AccountException as e:
            raise UnableToTakePayment(str(e))

        transfers.append((account, destination, amount))

    # All transfers verified, now redeem
    for account, destination, amount in transfers:
        facade.transfer(account, destination, amount,
                        user=user, merchant_reference=order_number,
                        description="Redeemed to pay for order %s" % order_number)


def create_giftcard(order_number, user, amount):
    source = core.paid_source_account()
    code = codes.generate()
    destination = Account.objects.create(
        code=code
    )
    facade.transfer(source, destination, amount, user,
                    "Create new account")
