from django.conf.urls.defaults import patterns, url
from django.views.decorators.csrf import csrf_exempt

from oscar.core.application import Application

from accounts.api import views, decorators


class APIApplication(Application):
    name = None

    accounts_view = views.AccountsView
    account_view = views.AccountView
    account_redemptions_view = views.AccountRedemptionsView
    account_refunds_view = views.AccountRefundsView

    transfer_view = views.TransferView
    transfer_reverse_view = views.TransferReverseView
    transfer_refunds_view = views.TransferRefundsView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^accounts/$',
                self.accounts_view.as_view(),
                name='accounts'),
            url(r'^accounts/(?P<code>[A-Z0-9]+)/$',
                self.account_view.as_view(),
                name='account'),
            url(r'^accounts/(?P<code>[A-Z0-9]+)/redemptions/$',
                self.account_redemptions_view.as_view(),
                name='account-redemptions'),
            url(r'^accounts/(?P<code>[A-Z0-9]+)/refunds/$',
                self.account_refunds_view.as_view(),
                name='account-refunds'),
            url(r'^transfers/(?P<reference>[A-Z0-9]{32})/$',
                self.transfer_view.as_view(),
                name='transfer'),
            url(r'^transfers/(?P<reference>[A-Z0-9]{32})/reverse/$',
                self.transfer_reverse_view.as_view(),
                name='transfer-reverse'),
            url(r'^transfers/(?P<reference>[A-Z0-9]{32})/refunds/$',
                self.transfer_refunds_view.as_view(),
                name='transfer-refunds'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return lambda x: csrf_exempt(decorators.basicauth(x))


application = APIApplication()
