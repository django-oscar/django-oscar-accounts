from decimal import Decimal as D

from django import forms
from django.conf import settings
from django.core import exceptions
from django.utils.translation import gettext_lazy as _
from oscar.core.loading import get_model
from oscar.forms.widgets import DatePickerInput
from oscar.templatetags.currency_filters import currency

from oscar_accounts import codes, names

Account = get_model('oscar_accounts', 'Account')
AccountType = get_model('oscar_accounts', 'AccountType')


class SearchForm(forms.Form):
    name = forms.CharField(required=False)
    code = forms.CharField(required=False)
    STATUS_CHOICES = (
        ('', "------"),
        (Account.OPEN, _("Open")),
        (Account.FROZEN, _("Frozen")),
        (Account.CLOSED, _("Closed")))
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)


class TransferSearchForm(forms.Form):
    reference = forms.CharField(required=False)
    start_date = forms.DateField(required=False, widget=DatePickerInput)
    end_date = forms.DateField(required=False, widget=DatePickerInput)


class EditAccountForm(forms.ModelForm):
    name = forms.CharField(label=_("Name"), required=True)

    class Meta:
        model = Account
        exclude = ['status', 'code', 'credit_limit', 'balance']
        widgets = {
            'start_date': DatePickerInput,
            'end_date': DatePickerInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product_range'].help_text = (
            "You may need to create a product range first")

        # Add field for account type (if there is a choice)
        deferred_income = AccountType.objects.get(name=names.DEFERRED_INCOME)
        types = deferred_income.get_children()
        if types.count() > 1:
            self.fields['account_type'] = forms.ModelChoiceField(
                queryset=types)
        elif types.count() == 1:
            del self.fields['account_type']
            self._account_type = types[0]
        else:
            raise exceptions.ImproperlyConfigured(
                "You need to define some 'deferred income' account types")


class SourceAccountMixin(object):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add field for source account (if there is a choice)
        unpaid_sources = AccountType.objects.get(
            name=names.UNPAID_ACCOUNT_TYPE)
        sources = unpaid_sources.accounts.all()
        if sources.count() > 1:
            self.fields['source_account'] = forms.ModelChoiceField(
                queryset=unpaid_sources.accounts.all())
        elif sources.count() == 1:
            self._source_account = sources[0]
        else:
            raise exceptions.ImproperlyConfigured(
                "You need to define some 'unpaid source' accounts")

    def get_source_account(self):
        if 'source_account' in self.cleaned_data:
            return self.cleaned_data['source_account']
        return self._source_account


class NewAccountForm(SourceAccountMixin, EditAccountForm):
    initial_amount = forms.DecimalField(
        min_value=getattr(settings, 'ACCOUNTS_MIN_LOAD_VALUE', D('0.00')),
        max_value=getattr(settings, 'ACCOUNTS_MAX_ACCOUNT_VALUE', None),
        decimal_places=2)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add field for source account (if there is a choice)
        unpaid_sources = AccountType.objects.get(
            name=names.UNPAID_ACCOUNT_TYPE)
        sources = unpaid_sources.accounts.all()
        if sources.count() > 1:
            self.fields['source_account'] = forms.ModelChoiceField(
                queryset=unpaid_sources.accounts.all())
        elif sources.count() == 1:
            self._source_account = sources[0]
        else:
            raise exceptions.ImproperlyConfigured(
                "You need to define some 'unpaid source' accounts")

    def save(self, *args, **kwargs):
        kwargs['commit'] = False
        account = super().save(*args, **kwargs)
        account.code = codes.generate()
        if hasattr(self, '_account_type'):
            account.account_type = self._account_type
        account.save()
        self.save_m2m()
        return account

    def get_source_account(self):
        if 'source_account' in self.cleaned_data:
            return self.cleaned_data['source_account']
        return self._source_account


class UpdateAccountForm(EditAccountForm):
    pass


class ChangeStatusForm(forms.ModelForm):
    status = forms.CharField(widget=forms.widgets.HiddenInput)
    new_status = None

    def __init__(self, *args, **kwargs):
        kwargs['initial']['status'] = self.new_status
        super().__init__(*args, **kwargs)

    class Meta:
        model = Account
        exclude = ['name', 'account_type', 'description', 'category', 'code', 'start_date',
                   'end_date', 'credit_limit', 'balance', 'product_range',
                   'primary_user', 'secondary_users',
                   'can_be_used_for_non_products']


class FreezeAccountForm(ChangeStatusForm):
    new_status = Account.FROZEN


class ThawAccountForm(ChangeStatusForm):
    new_status = Account.OPEN


class TopUpAccountForm(SourceAccountMixin, forms.Form):
    amount = forms.DecimalField(
        min_value=getattr(settings, 'ACCOUNTS_MIN_LOAD_VALUE', D('0.00')),
        max_value=getattr(settings, 'ACCOUNTS_MAX_ACCOUNT_VALUE', None),
        decimal_places=2)

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('instance')
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amt = self.cleaned_data['amount']
        if hasattr(settings, 'ACCOUNTS_MAX_ACCOUNT_VALUE'):
            max_amount = (
                settings.ACCOUNTS_MAX_ACCOUNT_VALUE - self.account.balance)
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


class WithdrawFromAccountForm(SourceAccountMixin, forms.Form):
    amount = forms.DecimalField(
        min_value=D('0.00'),
        max_value=None,
        decimal_places=2)

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('instance')
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amt = self.cleaned_data['amount']
        max_amount = self.account.balance
        if amt > max_amount:
            raise forms.ValidationError(_(
                "The account has only %s") % (
                    currency(max_amount)))
        return amt

    def clean(self):
        if self.account.is_closed():
            raise forms.ValidationError(_("Account is closed"))
        elif self.account.is_frozen():
            raise forms.ValidationError(_("Account is frozen"))
        return self.cleaned_data


class DateForm(forms.Form):
    date = forms.DateField(widget=DatePickerInput)


class DateRangeForm(forms.Form):
    start_date = forms.DateField(label=_("From"), widget=DatePickerInput)
    end_date = forms.DateField(label=_("To"), widget=DatePickerInput)
