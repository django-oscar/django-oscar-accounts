from django import forms
from django.utils.translation import gettext_lazy as _
from oscar.core.loading import get_model

Account = get_model('oscar_accounts', 'Account')


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
        return code
