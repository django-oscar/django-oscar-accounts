from django.views import generic
from django.core.urlresolvers import reverse
from django import http
from django.db.models import get_model
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

Account = get_model('accounts', 'Account')
from accounts import forms, facade


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
