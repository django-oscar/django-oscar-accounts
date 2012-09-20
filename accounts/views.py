from django.views import generic
from django.core.urlresolvers import reverse

from accounts.forms import AccountForm


class GETFormView(generic.FormView):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        # If any of the form keys are in the query params, validate form
        form_fields = set(self.form_class.base_fields.keys())
        if len(form_fields.intersection(set(request.GET.keys()))) > 0:
            return self.validate()
        return super(AccountBalanceView, self).get(request, *args, **kwargs)

    def validate(self):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = {'initial': self.get_initial()}
        if self.request.method == 'GET':
            kwargs.update({
                'data': self.request.GET,
            })
        return kwargs


class AccountBalanceView(GETFormView):
    form_class = AccountForm
    template_name = 'accounts/balance_check.html'

    def form_valid(self, form):
        ctx = self.get_context_data(form=form)
        ctx['account'] = form.account
        return self.render_to_response(ctx)
