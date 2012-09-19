from decimal import Decimal as D

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.db.models import get_model
from oscar.templatetags.currency_filters import currency

Account = get_model('accounts', 'Account')


class AccountForm(forms.Form):
    code = forms.CharField(label=_("Account code"))

    def clean_code(self):
        code = self.cleaned_data['code'].strip()
        try:
            self.account = Account.objects.get(
                code=code)
        except Account.DoesNotExist:
            raise forms.ValidationError(_(
                "No account found with this code"))
        if not self.account.is_active():
            raise forms.ValidationError(_(
                "This account is no longer active"))
        if not self.account.is_open():
            raise forms.ValidationError(_(
                "This account is no longer open"))
        return code


class AllocationForm(forms.Form):
    amount = forms.DecimalField(label=_("Allocation"))

    def __init__(self, order_total_incl_tax, account, allocations,
                 *args, **kwargs):
        """
        :order_total_incl_tax: Order total
        :account: An account instance
        :allocations: A dict of code -> amount of allocations
        """
        self.order_total_incl_tax = order_total_incl_tax
        self.account = account
        self.allocations = allocations
        initial = {
            'amount': self.get_max_amount()}
        super(AllocationForm, self).__init__(initial=initial, *args, **kwargs)

    def get_max_amount(self):
        already_allocated = D('0.00')
        for amount in self.allocations.values():
            already_allocated += amount
        return min(self.account.balance,
                   self.order_total_incl_tax - already_allocated)

    def clean_amount(self):
        amt = self.cleaned_data.get('amount')
        max_allocation = self.get_max_amount()
        if amt > max_allocation:
            raise forms.ValidationError(_(
                "The maximum allocation is %s") % currency(
                    max_allocation))
        return amt
