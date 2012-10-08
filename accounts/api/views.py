import json
from decimal import Decimal as D, InvalidOperation

from dateutil import parser
from django import http
from django.conf import settings
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
    def __init__(self, code, *args, **kwargs):
        self.code = code
        super(ValidationError, self).__init__(*args, **kwargs)


class JSONView(generic.View):
    required_keys = ()
    optional_keys = ()

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
            return self.forbidden(code=e.code, msg=errors.message(e.code))
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
        for key in self.optional_keys:
            validator_method = 'clean_%s' % key
            if hasattr(self, validator_method):
                payload[key] = getattr(self, validator_method)(payload[key])
        if hasattr(self, 'clean'):
            getattr(self, 'clean')(payload)


class AccountsView(JSONView):
    """
    For creating new accounts
    """
    required_keys = ('start_date', 'end_date', 'amount')

    def clean_amount(self, value):
        try:
            amount = D(value)
        except InvalidOperation:
            raise InvalidPayload("'%s' is not a valid amount" % value)
        if amount < 0:
            raise InvalidPayload("Amount must be positive")
        if amount < getattr(settings, 'ACCOUNTS_MIN_LOAD_VALUE', D('0.00')):
            raise ValidationError(errors.AMOUNT_TOO_LOW)
        if hasattr(settings, 'ACCOUNTS_MAX_ACCOUNT_VALUE'):
            if amount > getattr(settings, 'ACCOUNTS_MAX_ACCOUNT_VALUE'):
                raise ValidationError(errors.AMOUNT_TOO_HIGH)
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

    def clean(self, payload):
        if payload['start_date'] > payload['end_date']:
            raise InvalidPayload(
                'Start date must be before end date')

    def valid_payload(self, payload):
        account = self.create_account(payload)
        self.load_account(account, payload)
        return self.created(reverse('account', kwargs={'code': account.code}))

    def create_account(self, payload):
        return Account.objects.create(
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
                'redemptions_url': reverse('account-redemptions',
                                           kwargs={'code': account.code}),
                'refunds_url': reverse('account-refunds',
                                           kwargs={'code': account.code})}
        return self.ok(data)


class AccountRedemptionsView(JSONView):
    required_keys = ('amount',)
    optional_keys = ('merchant_reference',)

    def clean_amount(self, value):
        try:
            amount = D(value)
        except InvalidOperation:
            raise InvalidPayload("'%s' is not a valid amount" % value)
        if amount < 0:
            raise InvalidPayload("Amount must be positive")
        return amount

    def valid_payload(self, payload):
        """
        Redeem an amount from the selected giftcard
        """
        account = get_object_or_404(Account, code=self.kwargs['code'])
        redemptions = Account.objects.get(name=names.REDEMPTIONS)
        try:
            transfer = facade.transfer(
                account, redemptions, payload['amount'],
                merchant_reference=payload.get('merchant_reference', None))
        except exceptions.AccountException:
            raise
        return self.created(reverse('transfer',
                                    kwargs={'reference': transfer.reference}))


class AccountRefundsView(JSONView):
    required_keys = ('amount',)
    optional_keys = ('merchant_reference',)

    def clean_amount(self, value):
        try:
            amount = D(value)
        except InvalidOperation:
            raise InvalidPayload("'%s' is not a valid amount" % value)
        if amount < 0:
            raise InvalidPayload("Amount must be positive")
        return amount

    def valid_payload(self, payload):
        account = get_object_or_404(Account, code=self.kwargs['code'])
        redemptions = Account.objects.get(name=names.REDEMPTIONS)
        try:
            transfer = facade.transfer(
                redemptions, account, payload['amount'],
                merchant_reference=payload.get('merchant_reference', None))
        except exceptions.AccountException:
            raise
        return self.created(reverse('transfer', kwargs={'reference':
                                                        transfer.reference}))


class TransferView(JSONView):

    def get(self, request, *args, **kwargs):
        transfer = get_object_or_404(Transfer, reference=kwargs['reference'])
        data = {'id': str(transfer.id),
                'source_code': transfer.source.code,
                'source_name': transfer.source.name,
                'destination_code': transfer.destination.code,
                'destination_name': transfer.destination.name,
                'amount': "%.2f" % transfer.amount,
                'datetime': transfer.date_created.isoformat(),
                'merchant_reference': transfer.merchant_reference,
                'description': transfer.description,
                'reverse_url': reverse(
                    'transfer-reverse',
                    kwargs={'reference': transfer.reference}),
                'refunds_url': reverse(
                    'transfer-refunds',
                    kwargs={'reference': transfer.reference})}
        return self.ok(data)


class TransferReverseView(JSONView):
    optional_keys = ('merchant_reference',)

    def valid_payload(self, payload):
        to_reverse = get_object_or_404(Transfer,
                                       reference=self.kwargs['reference'])
        merchant_reference = payload.get('merchant_reference', None)
        try:
            transfer = facade.reverse(to_reverse,
                                      merchant_reference=merchant_reference)
        except exceptions.AccountException:
            raise
        return self.created(reverse('transfer', kwargs={'reference':
                                                        transfer.reference}))


class TransferRefundsView(JSONView):
    required_keys = ('amount',)
    optional_keys = ('merchant_reference',)

    def clean_amount(self, value):
        try:
            amount = D(value)
        except InvalidOperation:
            raise InvalidPayload("'%s' is not a valid amount" % value)
        if amount < 0:
            raise InvalidPayload("Amount must be positive")
        return amount

    def valid_payload(self, payload):
        to_refund = get_object_or_404(Transfer,
                                      reference=self.kwargs['reference'])
        amount = payload['amount']
        max_refund = to_refund.max_refund()
        if amount > max_refund:
            return self.forbidden(
                ("Refund not permitted: maximum refund permitted "
                 "is %.2f") % max_refund)
        try:
            transfer = facade.transfer(
                to_refund.destination, to_refund.source,
                payload['amount'], parent=to_refund,
                merchant_reference=payload.get('merchant_reference', None))
        except exceptions.AccountException:
            raise
        return self.created(reverse('transfer',
                                    kwargs={'reference': transfer.reference}))
