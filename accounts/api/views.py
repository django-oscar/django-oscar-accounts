import json
from decimal import Decimal as D, InvalidOperation

from dateutil import parser
from django import http
from django.contrib.auth.models import User
from django.core import validators, exceptions as core_exceptions
from django.core.urlresolvers import reverse
from django.db.models import get_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import generic

from accounts.api import errors
from accounts import codes, names, facade, exceptions

Account = get_model('accounts', 'Account')
Transfer = get_model('accounts', 'Transfer')


class InvalidPayload(Exception):
    pass


class ValidationError(Exception):
    pass


class JSONView(generic.View):

    required_keys = ()

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

    # Success handlers

    def created(self, url):
        response = http.HttpResponse(status=201)
        response['Location'] = url
        return response

    def ok(self, data):
        return http.HttpResponse(json.dumps(data),
                                 content_type='application/json')

    def post(self, request, *args, **kwargs):
        # Only accept JSON
        if request.META['CONTENT_TYPE'] != 'application/json':
            return self.bad_request(
                msg="Requests must have CONTENT_TYPE 'application/json'")
        try:
            payload = json.loads(request.raw_post_data)
        except ValueError:
            return self.bad_request(
                msg="JSON payload could not be decoded")
        try:
            self.validate_payload(payload)
        except InvalidPayload, e:
            return self.bad_request(msg=str(e))
        except ValidationError, e:
            return self.forbidden(msg=str(e))
        return self.valid_payload(payload)

    def validate_payload(self, payload):
        # We mimic Django's forms API by using dynamic dispatch to call clean_*
        # methods, and use a single 'clean' method to validate relations
        # between fields.
        for key in self.required_keys:
            if key not in payload:
                raise InvalidPayload((
                    "Mandatory field '%s' is missing from JSON "
                    "payload") % key)
            validator_method = 'clean_%s' % key
            if hasattr(self, validator_method):
                payload[key] = getattr(self, validator_method)(payload[key])
        if hasattr(self, 'clean'):
            getattr(self, 'clean')(payload)


class AccountsView(JSONView):
    """
    For creating new accounts
    """
    required_keys = ('start_date', 'end_date', 'amount', 'user_id',
                     'user_email')

    def clean_amount(self, value):
        try:
            amount = D(value)
        except InvalidOperation:
            raise InvalidPayload("'%s' is not a valid amount" % value)
        if amount < 0:
            raise InvalidPayload("Amount must be positive")
        return amount

    def clean_start_date(self, value):
        start_date = parser.parse(value)
        if timezone.is_naive(start_date):
            raise InvalidPayload(
                'Start date must include timezone information')
        return start_date

    def clean_end_date(self, value):
        end_date = parser.parse(value)
        if timezone.is_naive(end_date):
            raise InvalidPayload(
                'End date must include timezone information')
        return end_date

    def clean_user_email(self, value):
        try:
            validators.validate_email(value)
        except core_exceptions.ValidationError:
            raise InvalidPayload("'%s' is not a valid email address" % value)
        return value

    def clean(self, payload):
        if payload['start_date'] > payload['end_date']:
            raise InvalidPayload(
                'Start date must be before end date')

    def valid_payload(self, payload):
        account = self.create_account(payload)
        self.load_account(account, payload)
        return self.created(reverse('account', kwargs={'code': account.code}))

    def create_account(self, payload):
        user = self.create_user(payload['user_id'],
                                payload['user_email'])
        return Account.objects.create(
            primary_user=user,
            start_date=payload['start_date'],
            end_date=payload['end_date'],
            code=codes.generate()
        )

    def load_account(self, account, payload):
        bank = Account.objects.get(name=names.BANK)
        try:
            facade.transfer(bank, account, payload['amount'],
                            description="Load from bank")
        except exceptions.AccountException:
            account.delete()
            # handle this and return a response
            raise

    def create_user(self, username, email):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(username, email, None)
        return user


class AccountView(JSONView):
    """
    Fetch details of an account
    """

    def get(self, request, *args, **kwargs):
        account = get_object_or_404(Account, code=kwargs['code'])
        data = {'code': account.code,
                'start_date': account.start_date.isoformat(),
                'end_date': account.end_date.isoformat(),
                'balance': "%.2f" % account.balance,
                'user_id': account.primary_user.username,
                'user_email': account.primary_user.email}
        return self.ok(data)


class AccountRedemptionsView(JSONView):

    def valid_payload(self, payload):
        """
        Redeem an amount from the selected giftcard
        """
        account = get_object_or_404(Account, code=self.kwargs['code'])
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


class AccountRefundsView(JSONView):

    def valid_payload(self, payload):
        account = get_object_or_404(Account, code=self.kwargs['code'])
        amount = D(payload['amount'])
        order_number = payload['order_number']

        redemptions = Account.objects.get(name=names.REDEMPTIONS)
        try:
            transfer = facade.transfer(redemptions, account, amount,
                                       order_number=order_number)
        except exceptions.AccountException:
            raise
        return self.created(reverse('transfer', kwargs={'pk': transfer.id}))


class TransferView(JSONView):

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
        return self.ok(data)


class TransferReverseView(JSONView):

    def valid_payload(self, payload):
        to_reverse = get_object_or_404(Transfer, id=self.kwargs['pk'])
        order_number = payload['order_number']
        try:
            transfer = facade.reverse(to_reverse, order_number=order_number)
        except exceptions.AccountException:
            raise
        return self.created(reverse('transfer', kwargs={'pk': transfer.id}))
