from decimal import Decimal as D

from django.contrib.auth.models import User
from django.db.models import Sum
from django.test import TestCase, TransactionTestCase
from django_dynamic_fixture import G
import mock

from budgets.models import Budget, Transaction, BudgetTransaction
from budgets import facade, exceptions


class TestASimpleTransfer(TestCase):

    def setUp(self):
        self.user = G(User)
        self.source = Budget.objects.create(credit_limit=None)
        self.destination = Budget.objects.create()
        self.txn = facade.transfer(self.source, self.destination, D('100'),
                              self.user, "Give money to customer")

    def test_records_the_authorising_user(self):
        self.assertEqual(self.user, self.txn.user)

    def test_can_record_a_description(self):
        self.assertEqual("Give money to customer", self.txn.description)

    def test_creates_two_budget_transactions(self):
        self.assertEqual(2, self.txn.budget_transactions.all().count())

    def test_preserves_zero_sum_invariant(self):
        aggregates = self.txn.budget_transactions.aggregate(sum=Sum('amount'))
        self.assertEqual(D('0.00'), aggregates['sum'])

    def test_debits_the_source_budget(self):
        self.assertEqual(D('-100.00'), self.source.balance())

    def test_credits_the_destination_budget(self):
        self.assertEqual(D('100.00'), self.destination.balance())

    def test_creates_a_credit_transaction(self):
        destination_txn = self.txn.budget_transactions.get(
            budget=self.destination)
        self.assertEqual(D('100.00'), destination_txn.amount)

    def test_creates_a_debit_transaction(self):
        source_txn = self.txn.budget_transactions.get(budget=self.source)
        self.assertEqual(D('-100.00'), source_txn.amount)


class TestErrorHandling(TransactionTestCase):

    def test_no_transaction_created_when_exception_raised(self):
        user = G(User)
        source = Budget.objects.create(credit_limit=None)
        destination = Budget.objects.create()
        with mock.patch(
            'budgets.abstract_models.TransactionManager._wrap') as mock_method:
            mock_method.side_effect = RuntimeError()
            try:
                facade.transfer(source, destination, D('100'), user)
            except Exception:
                pass
        self.assertEqual(0, Transaction.objects.all().count())
        self.assertEqual(0, BudgetTransaction.objects.all().count())

    def test_budget_exception_raised_for_invalid_transfer(self):
        user = G(User)
        source = Budget.objects.create()
        destination = Budget.objects.create()
        with self.assertRaises(exceptions.BudgetException):
            facade.transfer(source, destination, D('100'), user)

    def test_budget_exception_raised_for_runtime_error(self):
        user = G(User)
        source = Budget.objects.create(credit_limit=None)
        destination = Budget.objects.create()
        with mock.patch(
            'budgets.abstract_models.TransactionManager._wrap') as mock_method:
            mock_method.side_effect = RuntimeError()
            with self.assertRaises(exceptions.BudgetException):
                facade.transfer(source, destination, D('100'), user)
