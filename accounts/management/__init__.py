from accounts import models, names
from django.db.models import signals


def ensure_core_accounts_exists(sender, **kwargs):
    # We only create core accounts the first time syncdb is run
    if models.Account.objects.all().count() > 0:
        return

    # Default structure is:
    #
    # - Sales
    #   - Recognised income
    #     * Account redemptions (C)
    #     * Lapsed accounts (D)
    # - Assets
    #   - Cash
    #     * Bank
    # - Costs
    #   - Unpaid sources
    #     * eg "Customer services compensation" (B)
    #     * eg "Merchant funded"
    #     * ...
    # - Liabilities
    #   - Deferred income
    #     - Customer-service-created accounts
    #       * Account 1234 (A)
    #       * Account 1235
    #     - $10 accounts
    #       * Account 1234
    #       * Account 1235
    #     - $20 accounts
    #       * Account 1234
    #       * Account 1235

    # Typical stories:
    #
    # * Admin creates a new budget: (B->A)
    #   - create a new account with account-type "Customer-service-created accounts"
    #   - transfer from "Customer services compensation" to this account
    # * Customer redeems budget to pay for an order: (A->C)
    # * Budget expires and is closed (A->D)

    # Create asset accounts
    assets = models.AccountType.add_root(name='Assets')
    sales = assets.add_child(name="Sales")
    sales.accounts.create(name=names.REDEMPTIONS)
    sales.accounts.create(name=names.LAPSED)
    cash = assets.add_child(name=names.CASH)
    cash.accounts.create(name=names.BANK, credit_limit=None)
    unpaid = assets.add_child(name=names.UNPAID_ACCOUNT_TYPE)
    for name in names.UNPAID_ACCOUNTS:
        unpaid.accounts.create(name=name, credit_limit=None)

    # Create liability accounts
    liabilities = models.AccountType.add_root(name=names.LIABILITIES)
    income = liabilities.add_child(name=names.DEFERRED_INCOME)
    for name in names.DEFERRED_INCOME_ACCOUNT_TYPES:
        income.add_child(name=name)

signals.post_syncdb.connect(ensure_core_accounts_exists, sender=models)
