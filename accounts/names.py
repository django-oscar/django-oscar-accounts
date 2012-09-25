from django.conf import settings

# The basic name of the account.  Some projects will refer to them as
# giftcards, budgets or credit allocations
UNIT_NAME = getattr(settings, 'ACCOUNTS_UNIT_NAME', 'Giftcard')
UNIT_NAME_PLURAL = getattr(settings, 'ACCOUNTS_UNIT_NAME_PLURAL',
                           "%ss" % UNIT_NAME)

# Account where money is transferred to when an account is used to pay for an
# order.
REDEMPTIONS = getattr(settings, 'ACCOUNTS_REDEMPTIONS_NAME',
                      '%s redemptions' % settings.ACCOUNTS_UNIT_NAME)

# Account where money is transferred to when an account expires and is
# automatically closed
LAPSED = getattr(settings, 'ACCOUNTS_LAPSED_NAME',
                 'Lapsed %ss' % settings.ACCOUNTS_UNIT_NAME)

# Account which is used to transfer money into the system
MERCHANT_SOURCE = getattr(settings, 'ACCOUNTS_SOURCE_NAME',
                          "Unpaid source")
