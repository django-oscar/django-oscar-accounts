from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class OscarAccountsConfig(AppConfig):
    label = 'oscar_accounts'
    name = 'oscar_accounts'
    verbose_name = _('Accounts')
