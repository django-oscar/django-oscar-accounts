from decimal import Decimal as D

from django_webtest import WebTest
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from oscar.test.factories import UserFactory

from oscar_accounts import models
from tests.conftest import default_accounts


class TestAStaffMember(WebTest):

    def setUp(self):
        default_accounts()
        self.staff = UserFactory(is_staff=True)

    def test_can_browse_accounts(self):
        list_page = self.app.get(reverse('accounts-list'), user=self.staff)
        self.assertEqual(200, list_page.status_code)

    def test_can_create_a_new_account(self):
        list_page = self.app.get(reverse('accounts-list'), user=self.staff)
        create_page = list_page.click(linkid="create_new_account")
        create_page.form['name'] = 'Test account'
        create_page.form['initial_amount'] = '120.00'
        response = create_page.form.submit()
        self.assertEqual(302, response.status_code)

        acc = models.Account.objects.get(name='Test account')
        self.assertEqual(D('120.00'), acc.balance)
