from decimal import Decimal as D

from django.contrib.auth.models import User
from django.db.models import Sum
from django.test import TestCase, TransactionTestCase
from oscar.test.factories import UserFactory
import mock

from oscar_accounts import facade, exceptions
from oscar_accounts.models import Account, Transfer, Transaction
from oscar_accounts.test_factories import AccountFactory


class TestReversingATransfer(TestCase):

    def setUp(self):
        self.user = UserFactory()
        self.source = AccountFactory(primary_user=None, credit_limit=None)
        self.destination = AccountFactory(primary_user=None)
        self.transfer = facade.transfer(self.source, self.destination,
                                        D('100'), user=self.user,
                                        description="Give money to customer")
        self.reverse = facade.reverse(self.transfer, self.user,
                                      description="Oops! Return money")

    def test_creates_4_transactions(self):
        self.assertEqual(4, Transaction.objects.all().count())

    def test_creates_2_transfers(self):
        self.assertEqual(2, Transfer.objects.all().count())

    def test_leaves_both_balances_unchanged(self):
        self.assertEqual(D('0.00'), self.source.balance)
        self.assertEqual(D('0.00'), self.destination.balance)

    def test_records_the_authorising_user(self):
        self.assertEqual(self.user, self.reverse.user)

    def test_records_the_transfer_message(self):
        self.assertEqual("Oops! Return money", self.reverse.description)

    def test_records_the_correct_accounts(self):
        self.assertEqual(self.source, self.reverse.destination)
        self.assertEqual(self.destination, self.reverse.source)

    def test_records_the_correct_amount(self):
        self.assertEqual(D('100'), self.reverse.amount)


class TestATransfer(TestCase):

    def setUp(self):
        self.user = UserFactory()
        self.source = AccountFactory(credit_limit=None, primary_user=None)
        self.destination = AccountFactory()
        self.transfer = facade.transfer(
            self.source, self.destination, D('100'),
            user=self.user, description="Give money to customer")

    def test_generates_an_unguessable_reference(self):
        self.assertTrue(len(self.transfer.reference) > 0)

    def test_records_the_authorising_user(self):
        self.assertEqual(self.user, self.transfer.user)

    def test_can_record_a_description(self):
        self.assertEqual("Give money to customer", self.transfer.description)

    def test_creates_two_transactions(self):
        self.assertEqual(2, self.transfer.transactions.all().count())

    def test_preserves_zero_sum_invariant(self):
        aggregates = self.transfer.transactions.aggregate(sum=Sum('amount'))
        self.assertEqual(D('0.00'), aggregates['sum'])

    def test_debits_the_source_account(self):
        self.assertEqual(D('-100.00'), self.source.balance)

    def test_credits_the_destination_account(self):
        self.assertEqual(D('100.00'), self.destination.balance)

    def test_creates_a_credit_transaction(self):
        destination_txn = self.transfer.transactions.get(
            account=self.destination)
        self.assertEqual(D('100.00'), destination_txn.amount)

    def test_creates_a_debit_transaction(self):
        source_txn = self.transfer.transactions.get(account=self.source)
        self.assertEqual(D('-100.00'), source_txn.amount)


class TestAnAnonymousTransaction(TestCase):

    def test_doesnt_explode(self):
        source = AccountFactory(credit_limit=None)
        destination = AccountFactory()
        facade.transfer(source, destination, D('1'))


class TestErrorHandling(TransactionTestCase):

    def tearDown(self):
        Account.objects.all().delete()

    def test_no_transaction_created_when_exception_raised(self):
        user = UserFactory()
        source = AccountFactory(credit_limit=None)
        destination = AccountFactory()
        with mock.patch(
            'oscar_accounts.abstract_models.PostingManager._wrap') as mock_method:
            mock_method.side_effect = RuntimeError()
            try:
                facade.transfer(source, destination, D('100'), user)
            except Exception:
                pass
        self.assertEqual(0, Transfer.objects.all().count())
        self.assertEqual(0, Transaction.objects.all().count())

    def test_account_exception_raised_for_invalid_transfer(self):
        user = UserFactory()
        source = AccountFactory(credit_limit=D('0.00'))
        destination = AccountFactory()
        with self.assertRaises(exceptions.AccountException):
            facade.transfer(source, destination, D('100'), user)

    def test_account_exception_raised_for_runtime_error(self):
        user = UserFactory()
        source = AccountFactory(credit_limit=None)
        destination = AccountFactory()
        with mock.patch(
            'oscar_accounts.abstract_models.PostingManager._wrap') as mock_method:
            mock_method.side_effect = RuntimeError()
            with self.assertRaises(exceptions.AccountException):
                facade.transfer(source, destination, D('100'), user)
