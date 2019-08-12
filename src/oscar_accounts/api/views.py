import json
from decimal import Decimal as D
from decimal import InvalidOperation

from dateutil import parser
from django import http
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views import generic
from oscar.core.loading import get_model

from oscar_accounts import codes, exceptions, facade, names
from oscar_accounts.api import errors

Account = get_model('oscar_accounts', 'Account')
AccountType = get_model('oscar_accounts', 'AccountType')
Transfer = get_model('oscar_accounts', 'Transfer')


class InvalidPayload(Exception):
    pass


class ValidationError(Exception):
    def __init__(self, code, *args, **kwargs):
        self.code = code
        super().__init__(*args, **kwargs)


class JSONView(generic.View):
    required_keys = ()
    optional_keys = ()

    # Error handlers

    def forbidden(self, code=None, msg=None):
        # Forbidden by business logic
        return self.error(403, code, msg)

    def bad_request(self, code=None, msg=None):
        # Bad syntax (eg missing keys)
        return self.error(400, code, msg)

    def error(self, status_code, code, msg):
        data = {'code': code if code is not None else '',
                'message': msg if msg is not None else errors.message(code)}
        return http.HttpResponse(json.dumps(data),
                                 status=status_code,
                                 content_type='application/json')

    # Success handlers

    def created(self, url, data):
        response = http.HttpResponse(
            json.dumps(data), content_type='application/json',
            status=201)
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
            payload = json.loads(request.body.decode('utf-8'))
        except ValueError:
            return self.bad_request(
                msg="JSON payload could not be decoded")
        try:
            self.validate_payload(payload)
        except InvalidPayload as e:
            return self.bad_request(msg=str(e))
        except ValidationError as e:
            return self.forbidden(code=e.code, msg=errors.message(e.code))
        # We can still get a ValidationError even if the payload itself is
        # valid.
        try:
            return self.valid_payload(payload)
        except ValidationError as e:
            return self.forbidden(code=e.code, msg=errors.message(e.code))

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
    required_keys = ('start_date', 'end_date', 'amount', 'account_type')

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

    def clean_account_type(self, value):
        # Name must be one from a predefined set of values
        if value not in names.DEFERRED_INCOME_ACCOUNT_TYPES:
            raise InvalidPayload('Unrecognised account type')
        try:
            acc_type = AccountType.objects.get(name=value)
        except AccountType.DoesNotExist:
            raise InvalidPayload('Unrecognised account type')
        return acc_type

    def clean(self, payload):
        if payload['start_date'] > payload['end_date']:
            raise InvalidPayload(
                'Start date must be before end date')

    def valid_payload(self, payload):
        account = self.create_account(payload)
        try:
            self.load_account(account, payload)
        except exceptions.AccountException as e:
            account.delete()
            return self.forbidden(
                code=errors.CANNOT_CREATE_ACCOUNT,
                msg=e.message)
        else:
            return self.created(
                reverse('oscar_accounts_api:account', kwargs={'code': account.code}),
                account.as_dict())

    def create_account(self, payload):
        return Account.objects.create(
            account_type=payload['account_type'],
            start_date=payload['start_date'],
            end_date=payload['end_date'],
            code=codes.generate()
        )

    def load_account(self, account, payload):
        bank = Account.objects.get(name=names.BANK)
        facade.transfer(bank, account, payload['amount'],
                        description="Load from bank")


class AccountView(JSONView):
    """
    Fetch details of an account
    """
    def get(self, request, *args, **kwargs):
        account = get_object_or_404(Account, code=kwargs['code'])
        return self.ok(account.as_dict())


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
        if not account.is_active():
            raise ValidationError(errors.ACCOUNT_INACTIVE)
        amt = payload['amount']
        if not account.is_debit_permitted(amt):
            raise ValidationError(errors.INSUFFICIENT_FUNDS)

        redemptions = Account.objects.get(name=names.REDEMPTIONS)
        try:
            transfer = facade.transfer(
                account, redemptions, amt,
                merchant_reference=payload.get('merchant_reference', None))
        except exceptions.AccountException as e:
            return self.forbidden(
                code=errors.CANNOT_CREATE_TRANSFER,
                msg=e.message)
        return self.created(
            reverse('oscar_accounts_api:transfer', kwargs={'reference': transfer.reference}),
            transfer.as_dict())


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
        if not account.is_active():
            raise ValidationError(errors.ACCOUNT_INACTIVE)
        redemptions = Account.objects.get(name=names.REDEMPTIONS)
        try:
            transfer = facade.transfer(
                redemptions, account, payload['amount'],
                merchant_reference=payload.get('merchant_reference', None))
        except exceptions.AccountException as e:
            return self.forbidden(
                code=errors.CANNOT_CREATE_TRANSFER,
                msg=e.message)
        return self.created(
            reverse('oscar_accounts_api:transfer', kwargs={'reference': transfer.reference}),
            transfer.as_dict())


class TransferView(JSONView):
    def get(self, request, *args, **kwargs):
        transfer = get_object_or_404(Transfer, reference=kwargs['reference'])
        return self.ok(transfer.as_dict())


class TransferReverseView(JSONView):
    optional_keys = ('merchant_reference',)

    def valid_payload(self, payload):
        to_reverse = get_object_or_404(Transfer,
                                       reference=self.kwargs['reference'])
        if not to_reverse.source.is_active():
            raise ValidationError(errors.ACCOUNT_INACTIVE)
        merchant_reference = payload.get('merchant_reference', None)
        try:
            transfer = facade.reverse(to_reverse,
                                      merchant_reference=merchant_reference)
        except exceptions.AccountException as e:
            return self.forbidden(
                code=errors.CANNOT_CREATE_TRANSFER,
                msg=e.message)
        return self.created(
            reverse('oscar_accounts_api:transfer', kwargs={'reference': transfer.reference}),
            transfer.as_dict())


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
        if not to_refund.source.is_active():
            raise ValidationError(errors.ACCOUNT_INACTIVE)
        try:
            transfer = facade.transfer(
                to_refund.destination, to_refund.source,
                payload['amount'], parent=to_refund,
                merchant_reference=payload.get('merchant_reference', None))
        except exceptions.AccountException as e:
            return self.forbidden(
                code=errors.CANNOT_CREATE_TRANSFER,
                msg=e.message)
        return self.created(
            reverse('oscar_accounts_api:transfer', kwargs={'reference': transfer.reference}),
            transfer.as_dict())
