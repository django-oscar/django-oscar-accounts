from django.views import generic
from django.db.models import get_model

Account = get_model('accounts', 'Account')


class ListView(generic.ListView):
    model = Account
    context_object_name = 'accounts'
    template_name = 'dashboard/accounts/account_list.html'
