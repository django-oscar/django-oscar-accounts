import json
from decimal import Decimal as D

from django.views import generic
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django import http
from django.db.models import get_model
from dateutil import parser

from accounts.api import errors
from accounts import codes, names, facade, exceptions

Account = get_model('accounts', 'Account')
Transfer = get_model('accounts', 'Transfer')


class AccountsView(generic.View):

    # Error handlers
    def forbidden(self, code=None, msg=None):
        return self.error(403, code, msg)

    def bad_request(self, code=None, msg=None):
        return self.error(400, code, msg)

    def error(self, status_code, code, msg):
        data = {'code': code if code is not None else '',
                'message': msg if msg is not None else errors.message(code)}
        return http.HttpResponse(json.dumps(data),
                                 status=status_code,
                                 content_type='application/json')

    def post(self, request, *args, **kwargs):
        # Only accept JSON
        if request.META['CONTENT_TYPE'] != 'application/json':
            return http.HttpBadRequest(
                "Requests must have CONTENT_TYPE 'application/json'")

        try:
            payload = json.loads(request.raw_post_data)
        except ValueError:
            return http.HttpBadRequest(
                "JSON payload could not be decoded")

        # Validate the submission
        required_keys = ['start_date', 'end_date', 'amount']
        for key in required_keys:
            if key not in payload:
                return self.bad_request(
                    msg=("Mandatory field '%s' is missing from JSON "
                         "payload") % key)

        # TODO - validate these fields better
        start_date = parser.parse(payload['start_date'])
        end_date = parser.parse(payload['end_date'])
        amount = D(payload['amount'])

        # Create account
        account = Account.objects.create(
            start_date=start_date,
            end_date=end_date,
            code=codes.generate()
        )

        # Load account
        bank = Account.objects.get(name=names.BANK)
        try:
            facade.transfer(bank, account, amount,
                            description="Load from bank")
        except exceptions.AccountException, e:
            account.delete()
            # handle this and return a response
            raise

        response = http.HttpResponse(status=201)
        response['Location'] = reverse('account',
                                       kwargs={'code': account.code})
        return response


class AccountView(generic.View):

    def get(self, request, *args, **kwargs):
        account = Account.objects.get(code=kwargs['code'])
        data = {'code': account.code,
                'start_date': account.start_date.isoformat(),
                'end_date': account.end_date.isoformat(),
                'balance': "%.2f" % account.balance}
        return http.HttpResponse(json.dumps(data),
                                 content_type='application/json')


class AccountRedemptionsView(generic.View):

    def post(self, request, *args, **kwargs):
        """
        Redeem an amount from the selected giftcard
        """
        account = get_object_or_404(Account, code=kwargs['code'])

        # TODO Check request payload
        payload = json.loads(request.raw_post_data)
        amount = D(payload['amount'])
        order_number = D(payload['order_number'])

        redemptions = Account.objects.get(name=names.REDEMPTIONS)
        try:
            transfer = facade.transfer(account, redemptions, amount,
                                       order_number=order_number)
        except exceptions.AccountException:
            raise

        response = http.HttpResponse(status=201)
        response['Location'] = reverse(
            'transfer', kwargs={'pk': transfer.id})
        return response


class AccountRefundsView(generic.View):

    def post(self, request, *args, **kwargs):
        account = get_object_or_404(Account, code=kwargs['code'])

        # TODO Check request payload
        payload = json.loads(request.raw_post_data)
        amount = D(payload['amount'])
        order_number = payload['order_number']

        redemptions = Account.objects.get(name=names.REDEMPTIONS)
        try:
            transfer = facade.transfer(redemptions, account, amount,
                                       order_number=order_number)
        except exceptions.AccountException:
            raise

        response = http.HttpResponse(status=201)
        response['Location'] = reverse(
            'transfer', kwargs={'pk': transfer.id})
        return response


class TransferView(generic.View):

    def get(self, request, *args, **kwargs):
        transfer = get_object_or_404(Transfer, id=kwargs['pk'])
        data = {'id': str(transfer.id),
                'source_code': transfer.source.code,
                'source_name': transfer.source.name,
                'destination_code': transfer.destination.code,
                'destination_name': transfer.destination.name,
                'amount': "%.2f" % transfer.amount,
                'datetime': transfer.date_created.isoformat(),
                'order_number': transfer.order_number,
                'description': transfer.description}
        return http.HttpResponse(json.dumps(data),
                                 content_type='application/json')


class TransferReverseView(generic.View):

    def post(self, request, *args, **kwargs):
        to_reverse = get_object_or_404(Transfer, id=kwargs['pk'])
        payload = json.loads(request.raw_post_data)
        order_number = payload['order_number']
        try:
            transfer = facade.reverse(to_reverse, order_number=order_number)
        except exceptions.AccountException:
            raise

        response = http.HttpResponse(status=201)
        response['Location'] = reverse(
            'transfer', kwargs={'pk': transfer.id})
        return response
