from django.conf import settings

# The basic name of the account.  Some projects will refer to them as
# giftcards, budgets or credit allocations
UNIT_NAME = getattr(settings, 'ACCOUNTS_UNIT_NAME', 'Account')
UNIT_NAME_PLURAL = getattr(settings, 'ACCOUNTS_UNIT_NAME_PLURAL',
                           "%ss" % UNIT_NAME)

# Account where money is transferred to when an account is used to pay for an
# order.
REDEMPTIONS = getattr(settings, 'ACCOUNTS_REDEMPTIONS_NAME', 'Redemptions')

# Account where money is transferred to when an account expires and is
# automatically closed
LAPSED = getattr(settings, 'ACCOUNTS_LAPSED_NAME', 'Lapsed accounts')

UNPAID_ACCOUNTS = getattr(settings, 'ACCOUNTS_UNPAID_SOURCES',
                          ('Unpaid source',))

# Account where money is transferred from when creating a giftcard
BANK = getattr(settings, 'ACCOUNTS_BANK_NAME', "Bank")

# Account types
# =============

ASSETS = 'Assets'
SALES = 'Sales'
CASH = 'Cash'

# Accounts that hold money waiting to be spent
LIABILITIES = 'Liabilities'

UNPAID_ACCOUNT_TYPE = "Unpaid accounts"

DEFERRED_INCOME = "Deferred income"

DEFERRED_INCOME_ACCOUNT_TYPES = getattr(
    settings, 'ACCOUNTS_DEFERRED_INCOME_ACCOUNT_TYPES',
    ('Dashboard created accounts',))
