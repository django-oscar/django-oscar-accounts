import json

from django import test
from django.core.urlresolvers import reverse

from accounts import models


class TestCreatingAnAccountErrors(test.TestCase):

    def setUp(self):
        self.payload = {
            'start_date': '2013-01-01T09:00:00+03:00',
            'end_date': '2013-06-01T09:00:00+03:00',
            'amount': '400.00',
            'user_id': '1223',
            'user_email': 'david@example.com'
        }

    def post_json(self, payload):
        return self.client.post(
            reverse('accounts'), json.dumps(payload),
            content_type="application/json")

    def test_missing_dates(self):
        payload = self.payload.copy()
        del payload['start_date']
        response = self.post_json(payload)
        self.assertEqual(400, response.status_code)
        self.assertTrue('message' in json.loads(response.content))

    def test_timezone_naive_start_date(self):
        payload = self.payload.copy()
        payload['start_date'] = '2013-01-01T09:00:00'
        response = self.post_json(payload)
        self.assertEqual(400, response.status_code)
        self.assertTrue('message' in json.loads(response.content))

    def test_timezone_naive_end_date(self):
        payload = self.payload.copy()
        payload['end_date'] = '2013-06-01T09:00:00'
        response = self.post_json(payload)
        self.assertEqual(400, response.status_code)
        self.assertTrue('message' in json.loads(response.content))

    def test_dates_in_wrong_order(self):
        payload = self.payload.copy()
        payload['start_date'] = '2013-06-01T09:00:00+03:00'
        payload['end_date'] = '2013-01-01T09:00:00+03:00'
        response = self.post_json(payload)
        self.assertEqual(400, response.status_code)
        self.assertTrue('message' in json.loads(response.content))

    def test_invalid_amount(self):
        payload = self.payload.copy()
        payload['amount'] = 'silly'
        response = self.post_json(payload)
        self.assertEqual(400, response.status_code)
        self.assertTrue('message' in json.loads(response.content))

    def test_negative_amount(self):
        payload = self.payload.copy()
        payload['amount'] = '-100'
        response = self.post_json(payload)
        self.assertEqual(400, response.status_code)
        self.assertTrue('message' in json.loads(response.content))

    def test_invalid_email_address(self):
        payload = self.payload.copy()
        payload['user_email'] = 'silly @ domain . com'
        response = self.post_json(payload)
        self.assertEqual(400, response.status_code)
        self.assertTrue('message' in json.loads(response.content))


class TestSuccessfullyCreatingAnAccount(test.TestCase):

    def setUp(self):
        self.payload = {
            'start_date': '2013-01-01T09:00:00+03:00',
            'end_date': '2013-06-01T09:00:00+03:00',
            'amount': '400.00',
            'user_id': '1223',
            'user_email': 'david@example.com'
        }
        # Submit request to create a new account, then fetch the detail
        # page that is returned.
        self.create_response = self.client.post(
            reverse('accounts'), json.dumps(self.payload),
            content_type="application/json")
        if 'Location' in self.create_response:
            self.detail_response = self.client.get(
                self.create_response['Location'])
            self.payload = json.loads(self.detail_response.content)
            self.account = models.Account.objects.get(
                code=self.payload['code'])

    def test_returns_201(self):
        self.assertEqual(201, self.create_response.status_code)

    def test_returns_a_valid_location(self):
        self.assertEqual(200, self.detail_response.status_code)

    def test_detail_view_returns_correct_keys(self):
        keys = ['code', 'start_date', 'end_date', 'balance',
                'user_id', 'user_email']
        for key in keys:
            self.assertTrue(key in self.payload)

    def test_returns_dates_in_utc(self):
        self.assertEqual('2013-01-01T06:00:00+00:00',
                         self.payload['start_date'])
        self.assertEqual('2013-06-01T06:00:00+00:00',
                         self.payload['end_date'])

    def test_loads_the_account_with_the_right_amount(self):
        self.assertEqual('400.00', self.payload['balance'])

    def test_creates_a_primary_user(self):
        self.assertIsNotNone(self.account.primary_user)


class TestMakingARedemption(test.TestCase):

    def setUp(self):
        self.create_payload = {
            'start_date': '2013-01-01T09:00:00+03:00',
            'end_date': '2013-06-01T09:00:00+03:00',
            'amount': '400.00',
            'user_id': '1223',
            'user_email': 'david@example.com'
        }
        self.create_response = self.client.post(
            '/api/accounts/', json.dumps(self.create_payload),
            content_type="application/json")

        self.redeem_payload = {
            'amount': '50.00',
            'order_number': '1234'
        }
        redemption_url = self.create_response['Location'] + 'redemptions/'
        self.redeem_response = self.client.post(
            redemption_url,
            json.dumps(self.redeem_payload),
            content_type='application/json')

        transfer_url = self.redeem_response['Location']
        self.transfer_response = self.client.get(
            transfer_url)

    def test_returns_201_for_the_redeem_request(self):
        self.assertEqual(201, self.redeem_response.status_code)

    def test_returns_valid_transfer_url(self):
        url = self.redeem_response['Location']
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_returns_the_correct_data_in_the_transfer_request(self):
        data = json.loads(self.transfer_response.content)
        keys = ['source_code', 'source_name', 'destination_code',
                'destination_name', 'amount', 'datetime', 'order_number',
                'description']
        for key in keys:
            self.assertTrue(key in data, "Key '%s' not found in payload" % key)

        self.assertEqual('50.00', data['amount'])
        self.assertIsNone(data['destination_code'])


class TestTransferView(test.TestCase):

    def test_returns_404_for_missing_transfer(self):
        url = reverse('transfer', kwargs={'pk': 11111111})
        response = self.client.get(url)
        self.assertEqual(404, response.status_code)


class TestMakingARedemptionThenRefund(test.TestCase):

    def setUp(self):
        self.create_payload = {
            'start_date': '2013-01-01T09:00:00+03:00',
            'end_date': '2013-06-01T09:00:00+03:00',
            'amount': '400.00',
            'user_id': '1223',
            'user_email': 'david@example.com'
        }
        self.create_response = self.client.post(
            reverse('accounts'),
            json.dumps(self.create_payload),
            content_type="application/json")

        self.redeem_payload = {
            'amount': '50.00',
            'order_number': '1234'
        }
        redemption_url = self.create_response['Location'] + 'redemptions/'
        self.redeem_response = self.client.post(
            redemption_url,
            json.dumps(self.redeem_payload),
            content_type='application/json')

        self.refund_payload = {
            'amount': '25.00',
            'order_number': '1234',
        }
        refund_url = self.create_response['Location'] + 'refunds/'
        self.refund_response = self.client.post(
            refund_url,
            json.dumps(self.refund_payload),
            content_type='application/json')

    def test_returns_201_for_the_refund_request(self):
        self.assertEqual(201, self.refund_response.status_code)


class TestMakingARedemptionThenReverse(test.TestCase):

    def setUp(self):
        self.create_payload = {
            'start_date': '2013-01-01T09:00:00+03:00',
            'end_date': '2013-06-01T09:00:00+03:00',
            'amount': '400.00',
            'user_id': '1223',
            'user_email': 'david@example.com'
        }
        self.create_response = self.client.post(
            reverse('accounts'),
            json.dumps(self.create_payload),
            content_type="application/json")

        self.redeem_payload = {
            'amount': '50.00',
            'order_number': '1234'
        }
        redemption_url = self.create_response['Location'] + 'redemptions/'
        self.redeem_response = self.client.post(
            redemption_url,
            json.dumps(self.redeem_payload),
            content_type='application/json')

        self.reverse_payload = {
            'order_number': '1234',
        }
        reverse_url = self.redeem_response['Location'] + 'reverse/'
        self.reverse_response = self.client.post(
            reverse_url,
            json.dumps(self.reverse_payload),
            content_type='application/json')

    def test_returns_201_for_the_reverse_request(self):
        self.assertEqual(201, self.reverse_response.status_code)
