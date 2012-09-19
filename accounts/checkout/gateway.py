from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _
from oscar.apps.payment.exceptions import UnableToTakePayment

from accounts import facade, exceptions

Account = get_model('accounts', 'Account')
Transfer = get_model('accounts', 'Transfer')


def redeem(order_number, user, allocations):
    """
    Settle payment for the passed set of account allocations

    Will raise UnableToTakePayment if any of the transfers is invalid
    """
    # First, we need to check if the allocations are still valid.  The accounts
    # may have changed status since the allocations were written to the
    # session.
    transfers = []
    destination = facade.sales_account()
    for code, amount in allocations.items():
        try:
            account = Account.objects.get(code=code)
        except Account.DoesNotExist:
            raise UnableToTakePayment(
                _("No account found with code %s") % code)

        # We verify each transaction
        try:
            Transfer.objects.verify_transfer(
                account, destination, amount)
        except exceptions.AccountException, e:
            raise UnableToTakePayment(str(e))

        transfers.append((account, destination, amount))

    # All transfers verified, now redeem
    for account, destination, amount in transfers:
        facade.transfer(account, destination, amount,
                        user, "Redeemed to pay for order %s" % order_number)
