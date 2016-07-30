from oscar_accounts.compact_oscar import get_model

from oscar_accounts import names

Account = get_model('oscar_accounts', 'Account')


def redemptions_account():
    return Account.objects.get(name=names.REDEMPTIONS)


def lapsed_account():
    return Account.objects.get(name=names.LAPSED)
