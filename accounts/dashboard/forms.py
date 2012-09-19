from decimal import Decimal as D

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.db.models import get_model

Account = get_model('accounts', 'Account')

CATEGORIES = getattr(settings, 'ACCOUNTS_CATEGORIES', ())


class NewAccountForm(forms.ModelForm):
    name = forms.CharField(label=_("Name"), required=True)
    code = forms.RegexField(
        label=_("Code"), required=True,
        regex=r'^[a-zA-Z0-9]{4,}$', help_text=_(
            "Codes must be 4 or more characters, no spaces"))

    if CATEGORIES:
        choices = [(c, _(c)) for c in CATEGORIES]
        category = forms.ChoiceField(label=_("Category"), required=True,
                                     choices=choices)

    initial_amount = forms.DecimalField(
        min_value=getattr(settings, 'ACCOUNTS_MIN_INITIAL_VALUE', D('0.00')),
        max_value=getattr(settings, 'ACCOUNTS_MAX_INITIAL_VALUE', None),
        decimal_places=2)

    class Meta:
        model = Account
        exclude = ['status', 'credit_limit', 'balance', 'product_range',
                   'primary_user', 'secondary_users']
        if not CATEGORIES:
            exclude.append('category')
