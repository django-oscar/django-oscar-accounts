from decimal import Decimal as D

from django.contrib.auth.models import User
from django.db.models import Sum
from django.test import TestCase
from django_dynamic_fixture import G

from budgets.models import Budget
from budgets import facade


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
