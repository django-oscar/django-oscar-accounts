from decimal import Decimal as D
import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import G

from accounts import exceptions
from accounts.models import Account, Transfer


class TestASuccessfulTransfer(TestCase):

    def setUp(self):
        self.user = G(User, username="barry")
        self.source = Account.objects.create(credit_limit=None)
        self.destination = Account.objects.create()
        self.transfer = Transfer.objects.create(self.source, self.destination,
                                                D('10.00'), self.user)

    def test_creates_2_transactions(self):
        self.assertEqual(2, self.transfer.transactions.all().count())

    def test_updates_source_balance(self):
        self.assertEqual(-D('10.00'), self.source.balance)

    def test_updates_destination_balance(self):
        self.assertEqual(D('10.00'), self.destination.balance)

    def test_cannot_be_deleted(self):
        with self.assertRaises(RuntimeError):
            self.transfer.delete()

    def test_records_static_user_information_in_case_user_is_deleted(self):
        self.assertEqual('barry', self.transfer.authorisor_username)
        self.user.delete()
        transfer = Transfer.objects.get(id=self.transfer.id)
        self.assertEqual('barry', transfer.authorisor_username)


class TestATransferToAnInactiveAccount(TestCase):

    def test_is_permitted(self):
        self.user = G(User)
        today = datetime.date.today()
        source = Account.objects.create(credit_limit=None)
        destination = Account.objects.create(
            end_date=today - datetime.timedelta(days=1))
        try:
            Transfer.objects.create(source, destination,
                                    D('20.00'), self.user)
        except exceptions.AccountException, e:
            self.fail("Transfer failed: %s" % e)


class TestAnAttemptedTransfer(TestCase):

    def setUp(self):
        self.user = G(User)

    def test_raises_an_exception_when_trying_to_exceed_credit_limit_of_source(self):
        source = Account.objects.create(credit_limit=D('10.00'))
        destination = Account.objects.create()
        with self.assertRaises(exceptions.InsufficientFunds):
            Transfer.objects.create(source, destination,
                                    D('20.00'), self.user)

    def test_raises_an_exception_when_trying_to_debit_negative_value(self):
        source = Account.objects.create(credit_limit=None)
        destination = Account.objects.create()
        with self.assertRaises(exceptions.InvalidAmount):
            Transfer.objects.create(source, destination,
                                    D('-20.00'), self.user)

    def test_raises_an_exception_when_trying_to_use_inactive_source(self):
        today = datetime.date.today()
        source = Account.objects.create(credit_limit=None,
            end_date=today - datetime.timedelta(days=1))
        destination = Account.objects.create()
        with self.assertRaises(exceptions.InactiveAccount):
            Transfer.objects.create(source, destination,
                                    D('20.00'), self.user)

    def test_raises_an_exception_when_trying_to_use_closed_source(self):
        source = Account.objects.create(credit_limit=None)
        source.close()
        destination = Account.objects.create()
        with self.assertRaises(exceptions.ClosedAccount):
            Transfer.objects.create(source, destination,
                                       D('20.00'), self.user)

    def test_raises_an_exception_when_trying_to_use_closed_destination(self):
        source = Account.objects.create(credit_limit=None)
        destination = Account.objects.create()
        destination.close()
        with self.assertRaises(exceptions.ClosedAccount):
            Transfer.objects.create(source, destination,
                                    D('20.00'), self.user)
