from django.urls import path, re_path
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from oscar.core.application import OscarConfig

from oscar_accounts.api import decorators


class AccountsAPIConfig(OscarConfig):
    name = 'oscar_accounts.api'
    verbose_name = _('Accounts API')
    label = 'oscar_accounts_api'
    namespace = 'oscar_accounts_api'

    def ready(self):
        from oscar_accounts.api import views

        self.accounts_view = views.AccountsView
        self.account_view = views.AccountView
        self.account_redemptions_view = views.AccountRedemptionsView
        self.account_refunds_view = views.AccountRefundsView

        self.transfer_view = views.TransferView
        self.transfer_reverse_view = views.TransferReverseView
        self.transfer_refunds_view = views.TransferRefundsView

    def get_urls(self):
        urls = [
            path('accounts/', self.accounts_view.as_view(), name='accounts'),
            path('accounts/<str:code>/', self.account_view.as_view(), name='account'),
            path(
                'accounts/<str:code>/redemptions/',
                self.account_redemptions_view.as_view(),
                name='account-redemptions'
            ),
            path('accounts/<str:code>/refunds/', self.account_refunds_view.as_view(), name='account-refunds'),
            re_path(
                r'^transfers/(?P<reference>[A-Z0-9]{32})/$',
                self.transfer_view.as_view(),
                name='transfer'
            ),
            re_path(
                r'^transfers/(?P<reference>[A-Z0-9]{32})/reverse/$',
                self.transfer_reverse_view.as_view(),
                name='transfer-reverse'
            ),
            re_path(
                r'^transfers/(?P<reference>[A-Z0-9]{32})/refunds/$',
                self.transfer_refunds_view.as_view(),
                name='transfer-refunds'
            ),
        ]
        return self.post_process_urls(urls)

    def get_url_decorator(self, url_name):
        return lambda x: csrf_exempt(decorators.basicauth(x))
