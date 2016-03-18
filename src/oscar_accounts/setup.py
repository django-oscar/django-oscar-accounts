from oscar.core.loading import get_model


def create_default_accounts():
    """Create the default structure"""
    from oscar_accounts import names
    AccountType = get_model('oscar_accounts', 'AccountType')

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
    for i, name in enumerate(names.DEFERRED_INCOME_ACCOUNT_TYPES):
        income.add_child(name=name)
