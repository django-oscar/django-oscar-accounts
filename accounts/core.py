from django.db.models import get_model

from accounts import names

Account = get_model('accounts', 'Account')


def unpaid_source_account():
    return Account.objects.get(name=names.MERCHANT_SOURCE)


def paid_source_account():
    return Account.objects.get(name=names.CUSTOMER_SOURCE)


def redemptions_account():
    return Account.objects.get(name=names.REDEMPTIONS)


def lapsed_account():
    return Account.objects.get(name=names.LAPSED)
