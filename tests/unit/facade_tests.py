from decimal import Decimal as D

from django.contrib.auth.models import User
from django.db.models import Sum
from django.test import TestCase, TransactionTestCase
from django_dynamic_fixture import G
import mock

from accounts.models import Account, Transfer, Transaction
from accounts import facade, exceptions


class TestReversingATransfer(TestCase):

    def setUp(self):
        self.user = G(User)
        self.source = Account.objects.create(credit_limit=None)
        self.destination = Account.objects.create()
        self.transfer = facade.transfer(self.source, self.destination,
                                        D('100'), self.user, "Give money to customer")
        self.reverse = facade.reverse(self.transfer, self.user,
                                      "Oops! Return money")

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
        self.user = G(User)
        self.source = Account.objects.create(credit_limit=None)
        self.destination = Account.objects.create()
        self.transfer = facade.transfer(self.source, self.destination, D('100'),
                                        self.user, "Give money to customer")

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
        source = Account.objects.create(credit_limit=None)
        destination = Account.objects.create()
        facade.transfer(source, destination, D('1'))


class TestErrorHandling(TransactionTestCase):

    def test_no_transaction_created_when_exception_raised(self):
        user = G(User)
        source = Account.objects.create(credit_limit=None)
        destination = Account.objects.create()
        with mock.patch(
            'accounts.abstract_models.PostingManager._wrap') as mock_method:
            mock_method.side_effect = RuntimeError()
            try:
                facade.transfer(source, destination, D('100'), user)
            except Exception:
                pass
        self.assertEqual(0, Transfer.objects.all().count())
        self.assertEqual(0, Transaction.objects.all().count())

    def test_account_exception_raised_for_invalid_transfer(self):
        user = G(User)
        source = Account.objects.create()
        destination = Account.objects.create()
        with self.assertRaises(exceptions.AccountException):
            facade.transfer(source, destination, D('100'), user)

    def test_account_exception_raised_for_runtime_error(self):
        user = G(User)
        source = Account.objects.create(credit_limit=None)
        destination = Account.objects.create()
        with mock.patch(
            'accounts.abstract_models.PostingManager._wrap') as mock_method:
            mock_method.side_effect = RuntimeError()
            with self.assertRaises(exceptions.AccountException):
                facade.transfer(source, destination, D('100'), user)
