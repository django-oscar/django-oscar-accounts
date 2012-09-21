from django.db.models.signals import post_syncdb

from accounts import models, names


def ensure_core_accounts_exists(sender, **kwargs):
    # We only create core accounts the first time syncdb is run
    if models.Account.objects.all().count() > 0:
        return

    # Create asset accounts
    assets = models.AccountType.add_root(name='Assets')
    assets.accounts.create(name=names.REDEMPTIONS)
    assets.accounts.create(name=names.LAPSED)

    # Create liability accounts
    liabilities = models.AccountType.add_root(name='Liabilities')
    liabilities.accounts.create(name=names.MERCHANT_SOURCE,
                                credit_limit=None)
    liabilities.add_child(name="Giftcards")
    liabilities.add_child(name="User accounts")


post_syncdb.connect(ensure_core_accounts_exists, sender=models)
