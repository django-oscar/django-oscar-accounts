from django.views import generic
from django.core.urlresolvers import reverse
from django import http
from django.db.models import get_model
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from accounts import forms, facade

Account = get_model('accounts', 'Account')
Transfer = get_model('accounts', 'Transfer')


class ListView(generic.ListView):
    model = Account
    context_object_name = 'accounts'
    template_name = 'dashboard/accounts/account_list.html'


class CreateView(generic.CreateView):
    model = Account
    context_object_name = 'account'
    template_name = 'dashboard/accounts/account_form.html'
    form_class = forms.NewAccountForm

    def form_valid(self, form):
        # Create new account and make a transfer from the global source account
        account = form.save()
        amount = form.cleaned_data['initial_amount']
        facade.transfer(facade.source(), account, amount,
                        user=self.request.user)
        messages.success(self.request, _("New account created"))
        return http.HttpResponseRedirect(reverse('accounts-list'))


class DetailView(generic.DetailView):
    model = Account
    context_object_name = 'account'
    template_name = 'dashboard/accounts/account_detail.html'


class TransferListView(generic.ListView):
    model = Transfer
    context_object_name = 'transfers'
    template_name = 'dashboard/accounts/transfer_list.html'


class TransferDetailView(generic.DetailView):
    model = Transfer
    context_object_name = 'transfer'
    template_name = 'dashboard/accounts/transfer_detail.html'
