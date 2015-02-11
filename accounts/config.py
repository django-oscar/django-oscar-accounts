from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import ugettext_lazy as _

from . import names


def create_core_accounts(app_config, **kwargs):
    # Create asset accounts
    AccountType = app_config.get_model('AccountType')

    assets = AccountType.add_root(name=names.ASSETS)
    sales = assets.add_child(name=names.SALES)
    sales.accounts.create(name=names.REDEMPTIONS)
    sales.accounts.create(name=names.LAPSED)

    cash = assets.add_child(name=names.CASH)
    cash.accounts.create(name=names.BANK, credit_limit=None)

    unpaid = assets.add_child(name=names.UNPAID_ACCOUNT_TYPE)
    for name in names.UNPAID_ACCOUNTS:
        unpaid.accounts.create(name=name, credit_limit=None)

    # Create liability accounts
    liabilities = AccountType.add_root(name=names.LIABILITIES)
    income = liabilities.add_child(name=names.DEFERRED_INCOME)
    for name in names.DEFERRED_INCOME_ACCOUNT_TYPES:
        income.add_child(name=name)


class AccountsConfig(AppConfig):
    label = 'accounts'
    name = 'accounts'
    verbose_name = _('Accounts')

    def ready(self):
        post_migrate.connect(create_core_accounts, sender=self)
