from django.urls import path, re_path
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
            path('', self.account_list_view.as_view(), name='accounts-list'),
            path('create/', self.account_create_view.as_view(), name='accounts-create'),
            path('<int:pk>/update/', self.account_update_view.as_view(), name='accounts-update'),
            path('<int:pk>/', self.account_transactions_view.as_view(), name='accounts-detail'),
            path('<int:pk>/freeze/', self.account_freeze_view.as_view(), name='accounts-freeze'),
            path('<int:pk>/thaw/', self.account_thaw_view.as_view(), name='accounts-thaw'),
            path('<int:pk>/top-up/', self.account_top_up_view.as_view(), name='accounts-top-up'),
            path('<int:pk>/withdraw/', self.account_withdraw_view.as_view(), name='accounts-withdraw'),
            path('transfers/', self.transfer_list_view.as_view(), name='transfers-list'),
            re_path(
                r'^transfers/(?P<reference>[A-Z0-9]{32})/$',
                self.transfer_detail_view.as_view(),
                name='transfers-detail'
            ),
            path('reports/deferred-income/', self.report_deferred_income.as_view(), name='report-deferred-income'),
            path('reports/profit-loss/', self.report_profit_loss.as_view(), name='report-profit-loss'),
        ]
        return self.post_process_urls(urls)
