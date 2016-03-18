from decimal import Decimal as D

from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from oscar.apps.checkout import views
from oscar.apps.payment import exceptions
from oscar.apps.payment.models import Source, SourceType

from oscar_accounts import exceptions as act_exceptions
from oscar_accounts import security
from oscar_accounts.checkout import forms, gateway
from oscar_accounts.checkout.allocation import Allocations


class PaymentDetailsView(views.PaymentDetailsView):

    # Override core methods

    def get_context_data(self, **kwargs):
        ctx = super(PaymentDetailsView, self).get_context_data(**kwargs)

        # Add variable to indicate if the user is blocked from paying with
        # accounts.
        ctx['is_blocked'] = security.is_blocked(self.request)

        form = forms.ValidAccountForm(self.request.user)
        ctx['account_form'] = form

        # Add accounts that are linked to this user
        if self.request.user.is_authenticated():
            ctx['user_accounts'] = gateway.user_accounts(self.request.user)

        # Add existing allocations to context
        allocations = self.get_account_allocations()
        ctx['account_allocations'] = allocations
        ctx['to_allocate'] = ctx['order_total_incl_tax'] - allocations.total

        return ctx

    def post(self, request, *args, **kwargs):
        # Intercept POST requests to look for attempts to allocate to an
        # account, or remove an allocation.
        action = self.request.POST.get('action', None)
        if action == 'select_account':
            return self.select_account(request)
        elif action == 'allocate':
            return self.add_allocation(request)
        elif action == 'remove_allocation':
            return self.remove_allocation(request)
        return super(PaymentDetailsView, self).post(request, *args, **kwargs)

    def handle_payment(self, order_number, total, **kwargs):
        # Override payment method to use accounts to pay for the order
        allocations = self.get_account_allocations()
        if allocations.total != total:
            raise exceptions.UnableToTakePayment(
                "Your account allocations do not cover the order total")

        try:
            gateway.redeem(order_number, self.request.user, allocations)
        except act_exceptions.AccountException:
            raise exceptions.UnableToTakePayment(
                "An error occurred with the account redemption")

        # If we get here, payment was successful.  We record the payment
        # sources and event to complete the audit trail for this order
        source_type, __ = SourceType.objects.get_or_create(
            name="Account")
        for code, amount in allocations.items():
            source = Source(
                source_type=source_type,
                amount_debited=amount, reference=code)
            self.add_payment_source(source)
        self.add_payment_event("Settle", total)

    # Custom form-handling methods

    def select_account(self, request):
        ctx = self.get_context_data()

        # Check for blocked users
        if security.is_blocked(request):
            messages.error(request,
                           "You are currently blocked from using accounts")
            return http.HttpResponseRedirect(
                reverse('checkout:payment-deatils'))

        # If account form has been submitted, validate it and show the
        # allocation form if the account has non-zero balance
        form = forms.ValidAccountForm(self.request.user,
                                      self.request.POST)
        ctx['account_form'] = form
        if not form.is_valid():
            security.record_failed_request(self.request)
            return self.render_to_response(ctx)

        security.record_successful_request(self.request)
        ctx['allocation_form'] = forms.AllocationForm(
            form.account, self.request.basket,
            ctx['shipping_total_incl_tax'],
            ctx['order_total_incl_tax'],
            self.get_account_allocations())
        return self.render_to_response(ctx)

    def add_allocation(self, request):
        # We have two forms to validate, first check the account form
        account_form = forms.ValidAccountForm(request.user,
                                              self.request.POST)
        if not account_form.is_valid():
            # Only manipulation can get us here
            messages.error(request,
                           _("An error occurred allocating from your account"))
            return http.HttpResponseRedirect(reverse(
                'checkout:payment-details'))

        # Account is still valid, now check requested allocation
        ctx = self.get_context_data()
        allocation_form = forms.AllocationForm(
            account_form.account, self.request.basket,
            ctx['shipping_total_incl_tax'],
            ctx['order_total_incl_tax'],
            self.get_account_allocations(),
            data=self.request.POST)
        if not allocation_form.is_valid():
            ctx = self.get_context_data()
            ctx['allocation_form'] = allocation_form
            ctx['account_form'] = account_form
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

    def get_account_allocations(self):
        return self.checkout_session._get('accounts', 'allocations',
                                          Allocations())

    def set_account_allocations(self, allocations):
        return self.checkout_session._set('accounts',
                                          'allocations', allocations)
