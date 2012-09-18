from django import forms
from django.utils.translation import ugettext_lazy as _
from django.db.models import get_model

Account = get_model('accounts', 'Account')


class NewAccountForm(forms.ModelForm):
    name = forms.CharField(label=_("Name"), required=True)
    code = forms.CharField(label=_("Code"), required=True)
    initial_amount = forms.DecimalField()

    class Meta:
        model = Account
        exclude = ('category', 'status', 'credit_limit', 'balance',
                   'primary_user', 'secondary_users')
