from django.views import generic

from accounts.forms import AccountForm
from accounts import security


class AccountBalanceView(generic.FormView):
    form_class = AccountForm
    template_name = 'accounts/balance_check.html'

    def get_context_data(self, **kwargs):
        ctx = super(AccountBalanceView, self).get_context_data(**kwargs)
        ctx['is_blocked'] = security.is_blocked(self.request)
        return ctx

    def post(self, request, *args, **kwargs):
        # Check for blocked users before trying to validate form
        if security.is_blocked(request):
            return self.get(request, *args, **kwargs)
        return super(AccountBalanceView, self).post(request, *args, **kwargs)

    def form_invalid(self, form):
        security.record_failed_request(self.request)
        return super(AccountBalanceView, self).form_invalid(form)

    def form_valid(self, form):
        security.record_successful_request(self.request)
        ctx = self.get_context_data(form=form)
        ctx['account'] = form.account
        return self.render_to_response(ctx)
