from oscar.app import Shop

from apps.checkout.app import application as checkout_app


class AccountsShop(Shop):
    # Override the checkout app so we can use our own views
    checkout_app = checkout_app


application = AccountsShop()
