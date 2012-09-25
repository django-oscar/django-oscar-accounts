from django.conf.urls.defaults import patterns, url
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import ugettext_lazy as _

from oscar.core.application import Application
from oscar.apps.dashboard.nav import register, Node

from accounts.dashboard import views
from accounts import names

node = Node(_("Accounts"))
node.add_child(Node(_(names.UNIT_NAME_PLURAL), 'code-accounts-list'))
node.add_child(Node(_('Transfers'), 'transfers-list'))
register(node, 100)


class AccountsDashboardApplication(Application):
    name = None

    # Code-account views
    code_account_list_view = views.CodeAccountListView
    code_account_create_view = views.CodeAccountCreateView
    code_account_update_view = views.CodeAccountUpdateView

    account_transactions_view = views.AccountTransactionsView
    account_freeze_view = views.AccountFreezeView
    account_thaw_view = views.AccountThawView
    account_top_up_view = views.AccountTopUpView

    transfer_list_view = views.TransferListView
    transfer_detail_view = views.TransferDetailView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^code-accounts/$', self.code_account_list_view.as_view(),
                name='code-accounts-list'),
            url(r'^code-accounts/create/$', self.code_account_create_view.as_view(),
                name='code-accounts-create'),
            url(r'^code-accounts/(?P<pk>\d+)/update/$', self.code_account_update_view.as_view(),
                name='code-accounts-update'),
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
