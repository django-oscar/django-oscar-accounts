from decimal import Decimal as D

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.db.models import get_model

from oscar.templatetags.currency_filters import currency

Account = get_model('accounts', 'Account')


class SearchForm(forms.Form):
    name = forms.CharField(required=False)
    code = forms.CharField(required=False)
    STATUS_CHOICES = (
        ('', "------"),
        (Account.OPEN, _("Open")),
        (Account.FROZEN, _("Frozen")),
        (Account.CLOSED, _("Closed")))
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)


class EditAccountForm(forms.ModelForm):
    name = forms.CharField(label=_("Name"), required=True)

    def __init__(self, *args, **kwargs):
        super(EditAccountForm, self).__init__(*args, **kwargs)
        self.fields['product_range'].help_text = (
            "You may need to create a product range first")

    class Meta:
        model = Account
        exclude = ['status', 'code', 'account_type', 'credit_limit',
                   'balance', 'primary_user', 'secondary_users']


class NewAccountForm(EditAccountForm):
    initial_amount = forms.DecimalField(
        min_value=getattr(settings, 'ACCOUNTS_MIN_LOAD_VALUE', D('0.00')),
        max_value=getattr(settings, 'ACCOUNTS_MAX_ACCOUNT_VALUE', None),
        decimal_places=2)

    def __init__(self, account_type, *args, **kwargs):
        self.account_type = account_type
        super(NewAccountForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        kwargs['commit'] = False
        account = super(NewAccountForm, self).save(*args, **kwargs)
        account.account_type = self.account_type
        account.save()
        return account


class UpdateAccountForm(EditAccountForm):
    pass


class ChangeStatusForm(forms.ModelForm):
    status = forms.CharField(widget=forms.widgets.HiddenInput)
    new_status = None

    def __init__(self, *args, **kwargs):
        kwargs['initial']['status'] = self.new_status
        super(ChangeStatusForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Account
        exclude = ['name', 'account_type', 'description', 'category', 'code', 'start_date',
                   'end_date', 'credit_limit', 'balance', 'product_range',
                   'primary_user', 'secondary_users']


class FreezeAccountForm(ChangeStatusForm):
    new_status = Account.FROZEN


class ThawAccountForm(ChangeStatusForm):
    new_status = Account.OPEN


class TopUpAccountForm(forms.Form):
    amount = forms.DecimalField(
        min_value=getattr(settings, 'ACCOUNTS_MIN_LOAD_VALUE', D('0.00')),
        max_value=getattr(settings, 'ACCOUNTS_MAX_ACCOUNT_VALUE', None),
        decimal_places=2)

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('instance')
        super(TopUpAccountForm, self).__init__(*args, **kwargs)

    def clean_amount(self):
        amt = self.cleaned_data['amount']
        max_amount = settings.ACCOUNTS_MAX_ACCOUNT_VALUE - self.account.balance
        if amt > max_amount:
            raise forms.ValidationError(_(
                "The maximum permitted top-up amount is %s") % (
                    currency(max_amount)))
        return amt

    def clean(self):
        if self.account.is_closed():
            raise forms.ValidationError(_("Account is closed"))
        elif self.account.is_frozen():
            raise forms.ValidationError(_("Account is frozen"))
        return self.cleaned_data
