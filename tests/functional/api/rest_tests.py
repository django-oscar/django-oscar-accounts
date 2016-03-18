import base64
import json
from decimal import Decimal as D

from oscar_accounts import models
from django import test
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.utils.encoding import force_bytes

from tests.conftest import default_accounts

USERNAME, PASSWORD = 'client', 'password'


def get_headers():
    # Create a user to authenticate as
    try:
        User.objects.get(username=USERNAME)
    except User.DoesNotExist:
        User.objects.create_user(USERNAME, None, PASSWORD)
    auth = "%s:%s" % (USERNAME, PASSWORD)
    auth_headers = {
        'HTTP_AUTHORIZATION': b'Basic ' + base64.b64encode(auth.encode('utf-8'))
    }
    return auth_headers


def get(url):
    return Client().get(url, **get_headers())


def post(url, payload):
    """
    POST a JSON-encoded payload
    """
    return Client().post(
        url, json.dumps(payload),
        content_type="application/json",
        **get_headers())


def to_json(response):
    return json.loads(response.content.decode('utf-8'))



class TestCreatingAnAccountErrors(test.TestCase):

    def setUp(self):
        default_accounts()
        self.payload = {
            'start_date': '2012-01-01T09:00:00+03:00',
            'end_date': '2019-06-01T09:00:00+03:00',
            'amount': '400.00',
        }

    def test_missing_dates(self):
        payload = self.payload.copy()
        del payload['start_date']
        response = post(reverse('accounts'), payload)
        self.assertEqual(400, response.status_code)
        self.assertTrue('message' in to_json(response))

    def test_timezone_naive_start_date(self):
        payload = self.payload.copy()
        payload['start_date'] = '2013-01-01T09:00:00'
        response = post(reverse('accounts'), payload)
        self.assertEqual(400, response.status_code)
        self.assertTrue('message' in to_json(response))

    def test_timezone_naive_end_date(self):
        payload = self.payload.copy()
        payload['end_date'] = '2013-06-01T09:00:00'
        response = post(reverse('accounts'), payload)
        self.assertEqual(400, response.status_code)
        self.assertTrue('message' in to_json(response))

    def test_dates_in_wrong_order(self):
        payload = self.payload.copy()
        payload['start_date'] = '2013-06-01T09:00:00+03:00'
        payload['end_date'] = '2013-01-01T09:00:00+03:00'
        response = post(reverse('accounts'), payload)
        self.assertEqual(400, response.status_code)
        self.assertTrue('message' in to_json(response))

    def test_invalid_amount(self):
        payload = self.payload.copy()
        payload['amount'] = 'silly'
        response = post(reverse('accounts'), payload)
        self.assertEqual(400, response.status_code)
        self.assertTrue('message' in to_json(response))

    def test_negative_amount(self):
        payload = self.payload.copy()
        payload['amount'] = '-100'
        response = post(reverse('accounts'), payload)
        self.assertEqual(400, response.status_code)
        self.assertTrue('message' in to_json(response))

    def test_amount_too_low(self):
        payload = self.payload.copy()
        payload['amount'] = '1.00'
        with self.settings(ACCOUNTS_MIN_LOAD_VALUE=D('25.00')):
            response = post(reverse('accounts'), payload)
        self.assertEqual(403, response.status_code)
        data = to_json(response)
        self.assertEqual('C101', data['code'])

    def test_amount_too_high(self):
        payload = self.payload.copy()
        payload['amount'] = '5000.00'
        with self.settings(ACCOUNTS_MAX_ACCOUNT_VALUE=D('500.00')):
            response = post(reverse('accounts'), payload)
        self.assertEqual(403, response.status_code)
        data = to_json(response)
        self.assertEqual('C102', data['code'])


class TestSuccessfullyCreatingAnAccount(test.TestCase):

    def setUp(self):
        default_accounts()
        self.payload = {
            'start_date': '2013-01-01T09:00:00+03:00',
            'end_date': '2019-06-01T09:00:00+03:00',
            'amount': '400.00',
            'account_type': 'Test accounts',
        }
        # Submit request to create a new account, then fetch the detail
        # page that is returned.
        self.create_response = post(reverse('accounts'), self.payload)
        if 'Location' in self.create_response:
            self.detail_response = get(
                self.create_response['Location'])
            self.payload = to_json(self.detail_response)
            self.account = models.Account.objects.get(
                code=self.payload['code'])

    def test_returns_201(self):
        self.assertEqual(201, self.create_response.status_code)

    def test_returns_a_valid_location(self):
        self.assertEqual(200, self.detail_response.status_code)

    def test_detail_view_returns_correct_keys(self):
        keys = ['code', 'start_date', 'end_date', 'balance']
        for key in keys:
            self.assertTrue(key in self.payload)

    def test_returns_dates_in_utc(self):
        self.assertEqual('2013-01-01T06:00:00+00:00',
                         self.payload['start_date'])
        self.assertEqual('2019-06-01T06:00:00+00:00',
                         self.payload['end_date'])

    def test_loads_the_account_with_the_right_amount(self):
        self.assertEqual('400.00', self.payload['balance'])

    def test_detail_view_returns_redemptions_url(self):
        self.assertTrue('redemptions_url' in self.payload)

    def test_detail_view_returns_refunds_url(self):
        self.assertTrue('refunds_url' in self.payload)


class TestMakingARedemption(test.TestCase):

    def setUp(self):
        default_accounts()
        self.create_payload = {
            'start_date': '2012-01-01T09:00:00+03:00',
            'end_date': '2019-06-01T09:00:00+03:00',
            'amount': '400.00',
            'account_type': 'Test accounts',
        }
        self.create_response = post(reverse('accounts'), self.create_payload)
        self.assertEqual(201, self.create_response.status_code)
        self.detail_response = get(self.create_response['Location'])
        redemption_url = to_json(self.detail_response)['redemptions_url']

        self.redeem_payload = {
            'amount': '50.00',
            'merchant_reference': '1234'
        }
        self.redeem_response = post(redemption_url, self.redeem_payload)

        transfer_url = self.redeem_response['Location']
        self.transfer_response = get(
            transfer_url)

    def test_returns_201_for_the_redeem_request(self):
        self.assertEqual(201, self.redeem_response.status_code)

    def test_returns_valid_transfer_url(self):
        url = self.redeem_response['Location']
        response = get(url)
        self.assertEqual(200, response.status_code)

    def test_returns_the_correct_data_in_the_transfer_request(self):
        data = to_json(self.transfer_response)
        keys = ['source_code', 'source_name', 'destination_code',
                'destination_name', 'amount', 'datetime', 'merchant_reference',
                'description']
        for key in keys:
            self.assertTrue(key in data, "Key '%s' not found in payload" % key)

        self.assertEqual('50.00', data['amount'])
        self.assertIsNone(data['destination_code'])

    def test_works_without_merchant_reference(self):
        self.redeem_payload = {
            'amount': '10.00',
        }
        redemption_url = to_json(self.detail_response)['redemptions_url']
        response = post(redemption_url, self.redeem_payload)
        self.assertEqual(201, response.status_code)


class TestTransferView(test.TestCase):

    def test_returns_404_for_missing_transfer(self):
        url = reverse('transfer', kwargs={'reference':
                                          '12345678123456781234567812345678'})
        response = get(url)
        self.assertEqual(404, response.status_code)


class TestMakingARedemptionThenRefund(test.TestCase):

    def setUp(self):
        default_accounts()
        self.create_payload = {
            'start_date': '2012-01-01T09:00:00+03:00',
            'end_date': '2019-06-01T09:00:00+03:00',
            'amount': '400.00',
            'account_type': 'Test accounts',
        }
        self.create_response = post(
            reverse('accounts'), self.create_payload)
        self.detail_response = get(self.create_response['Location'])

        self.redeem_payload = {
            'amount': '50.00',
            'merchant_reference': '1234'
        }
        account_dict = to_json(self.detail_response)
        redemption_url = account_dict['redemptions_url']
        self.redeem_response = post(redemption_url, self.redeem_payload)

        self.refund_payload = {
            'amount': '25.00',
            'merchant_reference': '1234',
        }
        refund_url = account_dict['refunds_url']
        self.refund_response = post(refund_url, self.refund_payload)

    def test_returns_201_for_the_refund_request(self):
        self.assertEqual(201, self.refund_response.status_code)

    def test_works_without_a_merchant_reference(self):
        self.refund_payload = {
            'amount': '25.00',
        }
        account_dict = to_json(self.detail_response)
        refund_url = account_dict['refunds_url']
        self.refund_response = post(refund_url, self.refund_payload)
        self.assertEqual(201, self.refund_response.status_code)


class TestMakingARedemptionThenReverse(test.TestCase):

    def setUp(self):
        default_accounts()
        self.create_payload = {
            'start_date': '2012-01-01T09:00:00+03:00',
            'end_date': '2019-06-01T09:00:00+03:00',
            'amount': '400.00',
            'account_type': 'Test accounts',
        }
        self.create_response = post(reverse('accounts'), self.create_payload)
        self.detail_response = get(self.create_response['Location'])
        account_dict = to_json(self.detail_response)
        self.redeem_payload = {
            'amount': '50.00',
            'merchant_reference': '1234'
        }
        redemption_url = account_dict['redemptions_url']
        self.redeem_response = post(redemption_url, self.redeem_payload)

        transfer_response = get(self.redeem_response['Location'])
        transfer_dict = to_json(transfer_response)
        self.reverse_payload = {}
        reverse_url = transfer_dict['reverse_url']
        self.reverse_response = post(reverse_url, self.reverse_payload)

    def test_returns_201_for_the_reverse_request(self):
        self.assertEqual(201, self.reverse_response.status_code)


class TestMakingARedemptionThenTransferRefund(test.TestCase):

    def setUp(self):
        default_accounts()
        self.create_payload = {
            'start_date': '2012-01-01T09:00:00+03:00',
            'end_date': '2019-06-01T09:00:00+03:00',
            'amount': '1000.00',
            'account_type': 'Test accounts',
        }
        self.create_response = post(
            reverse('accounts'), self.create_payload)
        self.detail_response = get(self.create_response['Location'])
        account_dict = to_json(self.detail_response)

        self.redeem_payload = {'amount': '300.00'}
        redemption_url = account_dict['redemptions_url']
        self.redeem_response = post(redemption_url, self.redeem_payload)
        self.transfer_response = get(self.redeem_response['Location'])
        transfer_dict = to_json(self.transfer_response)

        self.refund_payload = {
            'amount': '25.00',
        }
        refund_url = transfer_dict['refunds_url']
        self.refund_response = post(refund_url, self.refund_payload)

    def test_returns_201_for_the_refund_request(self):
        self.assertEqual(201, self.refund_response.status_code)

    def test_refunds_are_capped_at_value_of_redemption(self):
        # Make another redemption to ensure the redemptions account has enough
        # funds to attemp the below refund
        self.redeem_payload = {'amount': '300.00'}
        account_dict = to_json(self.detail_response)
        redemption_url = account_dict['redemptions_url']
        post(redemption_url, self.redeem_payload)

        self.refund_payload = {
            'amount': '280.00',
        }
        transfer_dict = to_json(self.transfer_response)
        refund_url = transfer_dict['refunds_url']
        response = post(refund_url, self.refund_payload)
        self.assertEqual(403, response.status_code)
