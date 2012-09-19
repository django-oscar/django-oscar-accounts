from decimal import Decimal as D

from oscar.apps.checkout import views
from django.contrib import messages
from django import http
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from accounts.checkout import forms
from accounts.checkout.allocation import Allocations


class PaymentDetailsView(views.PaymentDetailsView):

    def get_context_data(self, **kwargs):
        ctx = super(PaymentDetailsView, self).get_context_data(**kwargs)

        if 'code' in self.request.GET:
            form = forms.AccountForm(self.request.GET)
            if form.is_valid():
                ctx['allocation_form'] = forms.AllocationForm(
                    ctx['order_total_incl_tax'], form.account,
                    self.get_account_allocations())
        else:
            form = forms.AccountForm()
        ctx['account_form'] = form

        # Add existing allocations to context
        allocations = self.get_account_allocations()
        ctx['account_allocations'] = allocations
        ctx['to_allocate'] = ctx['order_total_incl_tax'] - allocations.total

        return ctx

    def post(self, request, *args, **kwargs):
        # Look for allocation parameteter
        action = self.request.POST.get('action', None)
        if action == 'allocate':
            return self.allocate_from_account(request)
        elif action == 'remove_allocation':
            return self.remove_allocation(request)
        return super(PaymentDetailsView, self).post(request, *args, **kwargs)

    def allocate_from_account(self, request):
        # We have two forms to validate, first check the account form
        account_form = forms.AccountForm(self.request.POST)
        if not account_form.is_valid():
            # Only manipulation can get us here
            messages.error(request,
                           _("An error occurred allocating from your account"))
            return http.HttpResponseRedirect(reverse(
                'checkout:payment-details'))

        # Account is still valid, now check requested allocation
        ctx = self.get_context_data()
        allocation_form = forms.AllocationForm(
            ctx['order_total_incl_tax'], account_form.account,
            self.get_account_allocations(),
            data=self.request.POST)
        if not allocation_form.is_valid():
            ctx = self.get_context_data()
            ctx['allocation_form'] = allocation_form
            return self.render_to_response(ctx)

        # Allocation is valid - record in session and reload page
        self.store_allocation_in_session(allocation_form)
        messages.success(request, _("Allocation recorded"))
        return http.HttpResponseRedirect(reverse(
            'checkout:payment-details'))

    def remove_allocation(self, request):
        code = None
        for key in request.POST.keys():
            if key.startswith('remove_'):
                code = key.replace('remove_', '')
        allocations = self.get_account_allocations()
        if not allocations.contains(code):
            messages.error(
                request, _("No allocation found with code '%s'") % code)
        else:
            allocations.remove(code)
            self.set_account_allocations(allocations)
            messages.success(request, _("Allocation removed"))
        return http.HttpResponseRedirect(reverse('checkout:payment-details'))

    def store_allocation_in_session(self, form):
        allocations = self.get_account_allocations()
        allocations.add(form.account.code, form.cleaned_data['amount'])
        self.set_account_allocations(allocations)

    # The below methods could be put onto a customised version of
    # oscar.apps.checkout.utils.CheckoutSessionData.  They are kept here for
    # simplicity

    def get_amount_allocated(self):
        total = D('0.00')
        for amount in self.get_account_allocations().values():
            total += amount
        return total

    def get_account_allocations(self):
        return self.checkout_session._get('accounts', 'allocations',
                                          Allocations())

    def set_account_allocations(self, allocations):
        return self.checkout_session._set('accounts',
                                          'allocations', allocations)
