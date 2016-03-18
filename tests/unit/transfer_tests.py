from decimal import Decimal as D

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from oscar.test.factories import UserFactory

from oscar_accounts import exceptions
from oscar_accounts.models import Account, Transfer
from oscar_accounts.test_factories import AccountFactory


class TestASuccessfulTransfer(TestCase):

    def setUp(self):
        self.user = UserFactory(username="barry")
        source = AccountFactory(primary_user=None, credit_limit=None)
        destination = AccountFactory()
        self.transfer = Transfer.objects.create(source, destination,
                                                D('10.00'), user=self.user)

    def test_creates_2_transactions(self):
        self.assertEqual(2, self.transfer.transactions.all().count())

    def test_records_the_transferred_amount(self):
        self.assertEqual(D('10.00'), self.transfer.amount)

    def test_updates_source_balance(self):
        self.assertEqual(-D('10.00'), self.transfer.source.balance)

    def test_updates_destination_balance(self):
        self.assertEqual(D('10.00'), self.transfer.destination.balance)

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
        self.user = UserFactory()
        now = timezone.now()
        source = AccountFactory(primary_user=None, credit_limit=None)
        destination = AccountFactory(end_date=now - timezone.timedelta(days=1))
        try:
            Transfer.objects.create(source, destination,
                                    D('20.00'), user=self.user)
        except exceptions.AccountException as e:
            self.fail("Transfer failed: %s" % e)


class TestATransferFromAnInactiveAccount(TestCase):

    def test_is_permitted(self):
        self.user = UserFactory()
        now = timezone.now()
        source = AccountFactory(
            credit_limit=None, primary_user=None,
            end_date=now - timezone.timedelta(days=1))
        destination = AccountFactory()
        try:
            Transfer.objects.create(
                source, destination, D('20.00'), user=self.user)
        except exceptions.AccountException as e:
            self.fail("Transfer failed: %s" % e)


class TestAnAttemptedTransfer(TestCase):

    def setUp(self):
        self.user = UserFactory()

    def test_raises_an_exception_when_trying_to_exceed_credit_limit_of_source(self):
        source = AccountFactory(primary_user=None, credit_limit=D('10.00'))
        destination = AccountFactory()
        with self.assertRaises(exceptions.InsufficientFunds):
            Transfer.objects.create(source, destination,
                                    D('20.00'), user=self.user)

    def test_raises_an_exception_when_trying_to_debit_negative_value(self):
        source = AccountFactory(credit_limit=None)
        destination = AccountFactory()
        with self.assertRaises(exceptions.InvalidAmount):
            Transfer.objects.create(source, destination,
                                    D('-20.00'), user=self.user)

    def test_raises_an_exception_when_trying_to_use_closed_source(self):
        source = AccountFactory(credit_limit=None)
        source.close()
        destination = AccountFactory()
        with self.assertRaises(exceptions.ClosedAccount):
            Transfer.objects.create(source, destination,
                                    D('20.00'), user=self.user)

    def test_raises_an_exception_when_trying_to_use_closed_destination(self):
        source = AccountFactory(primary_user=None, credit_limit=None)
        destination = AccountFactory()
        destination.close()
        with self.assertRaises(exceptions.ClosedAccount):
            Transfer.objects.create(
                source, destination, D('20.00'), user=self.user)
