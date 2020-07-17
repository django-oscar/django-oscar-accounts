import datetime
from decimal import Decimal as D

from django import http
from django.conf import settings
from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic
from oscar.core.loading import get_model
from oscar.templatetags.currency_filters import currency

from oscar_accounts import exceptions, facade, names
from oscar_accounts.dashboard import forms, reports

AccountType = get_model('oscar_accounts', 'AccountType')
Account = get_model('oscar_accounts', 'Account')
Transfer = get_model('oscar_accounts', 'Transfer')
Transaction = get_model('oscar_accounts', 'Transaction')


class AccountListView(generic.ListView):
    model = Account
    context_object_name = 'accounts'
    template_name = 'accounts/dashboard/account_list.html'
    form_class = forms.SearchForm
    description = _("All %s") % names.UNIT_NAME_PLURAL.lower()
    paginate_by = getattr(settings, 'OSCAR_ACCOUNTS_DASHBOARD_ITEMS_PER_PAGE', 20)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = self.form
        ctx['title'] = names.UNIT_NAME_PLURAL
        ctx['unit_name'] = names.UNIT_NAME
        ctx['queryset_description'] = self.description
        return ctx

    def get_queryset(self):
        queryset = Account.objects.all()

        if 'code' not in self.request.GET:
            # Form not submitted
            self.form = self.form_class()
            return queryset

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            # Form submitted but invalid
            return queryset

        # Form valid - build queryset and description
        data = self.form.cleaned_data
        desc_template = _(
            "%(status)s %(unit)ss %(code_filter)s %(name_filter)s")
        desc_ctx = {
            'unit': names.UNIT_NAME.lower(),
            'status': "All",
            'code_filter': "",
            'name_filter': "",
        }
        if data['name']:
            queryset = queryset.filter(name__icontains=data['name'])
            desc_ctx['name_filter'] = _(
                " with name matching '%s'") % data['name']
        if data['code']:
            queryset = queryset.filter(code=data['code'])
            desc_ctx['code_filter'] = _(
                " with code '%s'") % data['code']
        if data['status']:
            queryset = queryset.filter(status=data['status'])
            desc_ctx['status'] = data['status']

        self.description = desc_template % desc_ctx

        return queryset


class AccountCreateView(generic.CreateView):
    model = Account
    context_object_name = 'account'
    template_name = 'accounts/dashboard/account_form.html'
    form_class = forms.NewAccountForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = _("Create a new %s") % names.UNIT_NAME.lower()
        return ctx

    def form_valid(self, form):
        account = form.save()

        # Load transaction
        source = form.get_source_account()
        amount = form.cleaned_data['initial_amount']
        try:
            facade.transfer(source, account, amount,
                            user=self.request.user,
                            description=_("Creation of account"))
        except exceptions.AccountException as e:
            messages.error(
                self.request,
                _("Account created but unable to load funds onto new "
                  "account: %s") % e)
        else:
            messages.success(
                self.request,
                _("New account created with code '%s'") % account.code)
        return http.HttpResponseRedirect(
            reverse('accounts_dashboard:accounts-detail', kwargs={'pk': account.id}))


class AccountUpdateView(generic.UpdateView):
    model = Account
    context_object_name = 'account'
    template_name = 'accounts/dashboard/account_form.html'
    form_class = forms.UpdateAccountForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = _("Update '%s' account") % self.object.name
        return ctx

    def form_valid(self, form):
        account = form.save()
        messages.success(self.request, _("Account saved"))
        return http.HttpResponseRedirect(
            reverse('accounts_dashboard:accounts-detail', kwargs={'pk': account.id}))


class AccountFreezeView(generic.UpdateView):
    model = Account
    template_name = 'accounts/dashboard/account_freeze.html'
    form_class = forms.FreezeAccountForm

    def get_success_url(self):
        messages.success(self.request, _("Account frozen"))
        return reverse('accounts_dashboard:accounts-list')


class AccountThawView(generic.UpdateView):
    model = Account
    template_name = 'accounts/dashboard/account_thaw.html'
    form_class = forms.ThawAccountForm

    def get_success_url(self):
        messages.success(self.request, _("Account thawed"))
        return reverse('accounts_dashboard:accounts-list')


class AccountTopUpView(generic.UpdateView):
    model = Account
    template_name = 'accounts/dashboard/account_top_up.html'
    form_class = forms.TopUpAccountForm

    def form_valid(self, form):
        account = self.object
        amount = form.cleaned_data['amount']
        try:
            facade.transfer(form.get_source_account(), account, amount,
                            user=self.request.user,
                            description=_("Top-up account"))
        except exceptions.AccountException as e:
            messages.error(self.request,
                           _("Unable to top-up account: %s") % e)
        else:
            messages.success(
                self.request, _("%s added to account") % currency(amount))
        return http.HttpResponseRedirect(reverse('accounts_dashboard:accounts-detail',
                                                 kwargs={'pk': account.id}))


class AccountWithdrawView(generic.UpdateView):
    model = Account
    template_name = 'accounts/dashboard/account_withdraw.html'
    form_class = forms.WithdrawFromAccountForm

    def form_valid(self, form):
        account = self.object
        amount = form.cleaned_data['amount']
        try:
            facade.transfer(account, form.get_source_account(), amount,
                            user=self.request.user,
                            description=_("Return funds to source account"))
        except exceptions.AccountException as e:
            messages.error(self.request,
                           _("Unable to withdraw funds from account: %s") % e)
        else:
            messages.success(
                self.request,
                _("%s withdrawn from account") % currency(amount))
        return http.HttpResponseRedirect(reverse('accounts_dashboard:accounts-detail',
                                                 kwargs={'pk': account.id}))


class AccountTransactionsView(generic.ListView):
    model = Transaction
    context_object_name = 'transactions'
    template_name = 'accounts/dashboard/account_detail.html'
    paginate_by = getattr(settings, 'OSCAR_ACCOUNTS_DASHBOARD_ITEMS_PER_PAGE', 20)

    def get(self, request, *args, **kwargs):
        self.account = get_object_or_404(Account, id=kwargs['pk'])
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return self.account.transactions.all().order_by('-date_created')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['account'] = self.account
        return ctx


class TransferListView(generic.ListView):
    model = Transfer
    context_object_name = 'transfers'
    template_name = 'accounts/dashboard/transfer_list.html'
    form_class = forms.TransferSearchForm
    description = _("All transfers")
    paginate_by = getattr(settings, 'OSCAR_ACCOUNTS_DASHBOARD_ITEMS_PER_PAGE', 20)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = self.form
        ctx['queryset_description'] = self.description
        return ctx

    def get_queryset(self):
        queryset = self.model.objects.all()

        if 'reference' not in self.request.GET:
            # Form not submitted
            self.form = self.form_class()
            return queryset

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            # Form submitted but invalid
            return queryset

        # Form valid - build queryset and description
        data = self.form.cleaned_data
        desc_template = _(
            "Transfers %(reference)s %(date)s")
        desc_ctx = {
            'reference': "",
            'date': "",
        }
        if data['reference']:
            queryset = queryset.filter(reference=data['reference'])
            desc_ctx['reference'] = _(
                " with reference '%s'") % data['reference']

        if data['start_date'] and data['end_date']:
            # Add 24 hours to make search inclusive
            date_from = data['start_date']
            date_to = data['end_date'] + datetime.timedelta(days=1)
            queryset = queryset.filter(date_created__gte=date_from).filter(date_created__lt=date_to)
            desc_ctx['date'] = _(" created between %(start_date)s and %(end_date)s") % {
                'start_date': data['start_date'],
                'end_date': data['end_date']}
        elif data['start_date']:
            queryset = queryset.filter(date_created__gte=data['start_date'])
            desc_ctx['date'] = _(" created since %s") % data['start_date']
        elif data['end_date']:
            date_to = data['end_date'] + datetime.timedelta(days=1)
            queryset = queryset.filter(date_created__lt=date_to)
            desc_ctx['date'] = _(" created before %s") % data['end_date']

        self.description = desc_template % desc_ctx
        return queryset


class TransferDetailView(generic.DetailView):
    model = Transfer
    context_object_name = 'transfer'
    template_name = 'accounts/dashboard/transfer_detail.html'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return queryset.get(reference=self.kwargs['reference'])


class DeferredIncomeReportView(generic.FormView):
    form_class = forms.DateForm
    template_name = 'accounts/dashboard/reports/deferred_income.html'

    def get(self, request, *args, **kwargs):
        if self.is_form_submitted():
            return self.validate()
        return super().get(request, *args, **kwargs)

    def is_form_submitted(self):
        return 'date' in self.request.GET

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Deferred income report'
        return ctx

    def get_form_kwargs(self):
        kwargs = {'initial': self.get_initial()}
        if self.is_form_submitted():
            kwargs.update({
                'data': self.request.GET,
            })
        return kwargs

    def validate(self):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        # Take cutoff as the first second of the following day, which we
        # convert to a datetime instane in UTC
        threshold_date = form.cleaned_data['date'] + datetime.timedelta(days=1)
        threshold_datetime = datetime.datetime.combine(
            threshold_date, datetime.time(tzinfo=timezone.utc))

        # Get data
        rows = []
        totals = {'total': D('0.00'),
                  'num_accounts': 0}
        for acc_type_name in names.DEFERRED_INCOME_ACCOUNT_TYPES:
            acc_type = AccountType.objects.get(name=acc_type_name)
            data = {
                'name': acc_type_name,
                'total': D('0.00'),
                'num_accounts': 0,
                'num_expiring_within_30': 0,
                'num_expiring_within_60': 0,
                'num_expiring_within_90': 0,
                'num_expiring_outside_90': 0,
                'num_open_ended': 0,
                'total_expiring_within_30': D('0.00'),
                'total_expiring_within_60': D('0.00'),
                'total_expiring_within_90': D('0.00'),
                'total_expiring_outside_90': D('0.00'),
                'total_open_ended': D('0.00'),
            }
            for account in acc_type.accounts.all():
                data['num_accounts'] += 1
                total = account.transactions.filter(
                    date_created__lt=threshold_datetime).aggregate(
                        total=Sum('amount'))['total']
                if total is None:
                    total = D('0.00')
                data['total'] += total
                days_remaining = account.days_remaining(threshold_datetime)
                if days_remaining is None:
                    data['num_open_ended'] += 1
                    data['total_open_ended'] += total
                else:
                    if days_remaining <= 30:
                        data['num_expiring_within_30'] += 1
                        data['total_expiring_within_30'] += total
                    elif days_remaining <= 60:
                        data['num_expiring_within_60'] += 1
                        data['total_expiring_within_60'] += total
                    elif days_remaining <= 90:
                        data['num_expiring_within_90'] += 1
                        data['total_expiring_within_90'] += total
                    else:
                        data['num_expiring_outside_90'] += 1
                        data['total_expiring_outside_90'] += total

            totals['total'] += data['total']
            totals['num_accounts'] += data['num_accounts']
            rows.append(data)
        ctx = self.get_context_data(form=form)
        ctx['rows'] = rows
        ctx['totals'] = totals
        ctx['report_date'] = form.cleaned_data['date']
        return self.render_to_response(ctx)


class ProfitLossReportView(generic.FormView):
    form_class = forms.DateRangeForm
    template_name = 'accounts/dashboard/reports/profit_loss.html'

    def get(self, request, *args, **kwargs):
        if self.is_form_submitted():
            return self.validate()
        return super().get(request, *args, **kwargs)

    def is_form_submitted(self):
        return 'start_date' in self.request.GET

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Profit and loss report'
        return ctx

    def get_form_kwargs(self):
        kwargs = {'initial': self.get_initial()}
        if self.is_form_submitted():
            kwargs.update({
                'data': self.request.GET,
            })
        return kwargs

    def validate(self):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        start = form.cleaned_data['start_date']
        end = form.cleaned_data['end_date'] + datetime.timedelta(days=1)
        report = reports.ProfitLossReport(start, end)
        data = report.run()

        ctx = self.get_context_data(form=form)
        ctx.update(data)
        ctx['show_report'] = True
        ctx['start_date'] = start
        ctx['end_date'] = end

        return self.render_to_response(ctx)

    def total(self, qs):
        sales_amt = qs.aggregate(sum=Sum('amount'))['sum']
        return sales_amt if sales_amt is not None else D('0.00')
