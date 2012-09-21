from django.views import generic
from django.utils import timezone

from accounts.forms import AccountForm


class AccountBalanceView(generic.FormView):
    form_class = AccountForm
    template_name = 'accounts/balance_check.html'

    def form_invalid(self, form):
        return super(AccountBalanceView, self).form_invalid(form)

    def form_valid(self, form):
        ctx = self.get_context_data(form=form)
        ctx['account'] = form.account
        return self.render_to_response(ctx)
