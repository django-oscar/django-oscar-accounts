from django.conf.urls.defaults import patterns, url
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import ugettext_lazy as _

from oscar.core.application import Application
from oscar.apps.dashboard.nav import register, Node

from accounts.dashboard import views

node = Node(_('Accounts'))
node.add_child(Node(_('Code accounts'), 'accounts-list'))
node.add_child(Node(_('Transfers'), 'transfers-list'))
register(node, 100)


class AccountsDashboardApplication(Application):
    name = None
    account_list_view = views.AccountListView
    account_create_view = views.AccountCreateView
    account_update_view = views.AccountUpdateView
    account_transactions_view = views.AccountTransactionsView
    account_freeze_view = views.AccountFreezeView
    account_thaw_view = views.AccountThawView
    account_top_up_view = views.AccountTopUpView

    transfer_list_view = views.TransferListView
    transfer_detail_view = views.TransferDetailView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.account_list_view.as_view(),
                name='accounts-list'),
            url(r'^create/$', self.account_create_view.as_view(),
                name='accounts-create'),
            url(r'^(?P<pk>\d+)/update/$', self.account_update_view.as_view(),
                name='accounts-update'),
            url(r'^(?P<pk>\d+)/$', self.account_transactions_view.as_view(),
                name='accounts-detail'),
            url(r'^(?P<pk>\d+)/freeze/$', self.account_freeze_view.as_view(),
                name='accounts-freeze'),
            url(r'^(?P<pk>\d+)/thaw/$', self.account_thaw_view.as_view(),
                name='accounts-thaw'),
            url(r'^(?P<pk>\d+)/top-up/$', self.account_top_up_view.as_view(),
                name='accounts-top-up'),
            url(r'^transfers/$', self.transfer_list_view.as_view(),
                name='transfers-list'),
            url(r'^transfers/(?P<pk>\d+)/$',
                self.transfer_detail_view.as_view(),
                name='transfers-detail'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = AccountsDashboardApplication()
