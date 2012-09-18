from decimal import Decimal as D

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.db.models import get_model

Account = get_model('accounts', 'Account')


class NewAccountForm(forms.ModelForm):
    name = forms.CharField(label=_("Name"), required=True)
    code = forms.CharField(label=_("Code"), required=True)
    initial_amount = forms.DecimalField(
        min_value=getattr(settings, 'ACCOUNTS_MIN_INITIAL_VALUE', D('0.00')),
        max_value=getattr(settings, 'ACCOUNTS_MAX_INITIAL_VALUE', None),
        decimal_places=2)

    class Meta:
        model = Account
        exclude = ('category', 'status', 'credit_limit', 'balance',
                   'primary_user', 'secondary_users')
