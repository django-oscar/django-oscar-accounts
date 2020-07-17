from decimal import Decimal as D

from django import forms
from django.utils.translation import gettext_lazy as _
from oscar.core.loading import get_model
from oscar.templatetags.currency_filters import currency

Account = get_model('oscar_accounts', 'Account')


class ValidAccountForm(forms.Form):
    code = forms.CharField(label=_("Account code"))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_code(self):
        code = self.cleaned_data['code'].strip().upper()
        code = code.replace('-', '')
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
        if self.account.balance == D('0.00'):
            raise forms.ValidationError(_(
                "This account is empty"))
        if not self.account.can_be_authorised_by(self.user):
            raise forms.ValidationError(_(
                "You can not authorised to use this account"))
        return code


class AllocationForm(forms.Form):
    amount = forms.DecimalField(label=_("Allocation"), min_value=D('0.01'))

    def __init__(self, account, basket, shipping_total, order_total,
                 allocations, *args, **kwargs):
        """
        :account: Account to allocate from
        :basket: The basket to pay for
        :shipping_total: The shipping total
        :order_total: Order total
        :allocations: Allocations instance
        """
        self.account = account
        self.basket = basket
        self.shipping_total = shipping_total
        self.order_total = order_total
        self.allocations = allocations
        self.max_allocation = self.get_max_amount()
        initial = {'amount': self.max_allocation}
        super().__init__(initial=initial, *args, **kwargs)
        if self.account.product_range:
            self.fields['amount'].help_text = (
                "Restrictions apply to which products can be paid for")

    def get_max_amount(self):
        max_allocation = self.account.permitted_allocation(
            self.basket, self.shipping_total, self.order_total)
        return max_allocation - self.allocations.total

    def clean_amount(self):
        amt = self.cleaned_data.get('amount')
        max_allocation = self.max_allocation
        if amt > max_allocation:
            raise forms.ValidationError(_(
                "The maximum allocation is %s") % currency(
                    max_allocation))
        return amt
