from django.conf.urls import url
from oscar.core.application import OscarDashboardConfig


class AccountsDashboardConfig(OscarDashboardConfig):

    name = 'oscar_accounts.dashboard'
    label = 'accounts_dashboard'

    namespace = 'accounts_dashboard'

    default_permissions = ['is_staff']

    def ready(self):
        from . import views
        self.account_list_view = views.AccountListView
        self.account_create_view = views.AccountCreateView
        self.account_update_view = views.AccountUpdateView
        self.account_transactions_view = views.AccountTransactionsView
        self.account_freeze_view = views.AccountFreezeView
        self.account_thaw_view = views.AccountThawView
        self.account_top_up_view = views.AccountTopUpView
        self.account_withdraw_view = views.AccountWithdrawView

        self.transfer_list_view = views.TransferListView
        self.transfer_detail_view = views.TransferDetailView

        self.report_deferred_income = views.DeferredIncomeReportView
        self.report_profit_loss = views.ProfitLossReportView

    def get_urls(self):
        urls = [
            url(r'^$',
                self.account_list_view.as_view(),
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
            url(r'^(?P<pk>\d+)/withdraw/$', self.account_withdraw_view.as_view(),
                name='accounts-withdraw'),
            url(r'^transfers/$', self.transfer_list_view.as_view(),
                name='transfers-list'),
            url(r'^transfers/(?P<reference>[A-Z0-9]{32})/$',
                self.transfer_detail_view.as_view(),
                name='transfers-detail'),
            url(r'^reports/deferred-income/$',
                self.report_deferred_income.as_view(),
                name='report-deferred-income'),
            url(r'^reports/profit-loss/$',
                self.report_profit_loss.as_view(),
                name='report-profit-loss'),
        ]
        return self.post_process_urls(urls)
