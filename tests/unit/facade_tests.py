from decimal import Decimal as D

from django.contrib.auth.models import User
from django.db.models import Sum
from django.test import TestCase
from django_dynamic_fixture import G

from budgets.models import Budget, Transaction
from budgets import facade


class TestASimpleTransfer(TestCase):

    def test_records_the_authorising_user(self):
        authorisor = G(User)
        budgets = [Budget.objects.create(credit_limit=None),
                   Budget.objects.create()]
        facade.transfer(budgets[0], budgets[1], D('50'), authorisor)

        for txn in Transaction.objects.all():
            self.assertEqual(authorisor, txn.user)

    def test_returns_a_transaction_id_that_matches_the_transactions(self):
        authorisor = G(User)
        budgets = [Budget.objects.create(credit_limit=None),
                   Budget.objects.create()]
        txn_id = facade.transfer(budgets[0], budgets[1], D('50'), authorisor)
        self.assertEqual(2, Transaction.objects.filter(txn_id=txn_id).count())


class TestATransferFromCompanyBudgetToCustomer(TestCase):

    def setUp(self):
        staff_member = G(User, is_staff=True)
        self.source = Budget.objects.create(
            credit_limit=None,
            name="Company")

        customer = G(User, is_staff=False)
        self.destination = Budget.objects.create(
            primary_user=customer)

        facade.transfer(self.source, self.destination, D('100.00'),
                        staff_member)

        self.assertEqual(2, Transaction.objects.all().count())

    def test_creates_two_transactions(self):
        self.assertEqual(2, Transaction.objects.all().count())

    def test_preserves_zero_sum_invariant(self):
        aggregates = Transaction.objects.aggregate(sum=Sum('amount'))
        self.assertEqual(D('0.00'), aggregates['sum'])

    def test_debits_the_source_budget(self):
        self.assertEqual(D('-100.00'), self.source.balance())

    def test_credits_the_destination_budget(self):
        self.assertEqual(D('100.00'), self.destination.balance())

    def test_creates_a_credit_transaction(self):
        txn = self.source.transactions.all()[0]
        self.assertEqual(D('-100.00'), txn.amount)

    def test_creates_a_debit_transaction(self):
        txn = self.destination.transactions.all()[0]
        self.assertEqual(D('100.00'), txn.amount)


class TestPayingForAnOrderWithBudget(TestCase):

    def setUp(self):
        staff_member = G(User, is_staff=True)
        company_budget = Budget.objects.create(
            credit_limit=None,
            name="Company")

        customer = G(User, is_staff=False)
        self.customer_budget = Budget.objects.create(
            primary_user=customer)

        # Transfer some funds to customer from company
        facade.transfer(company_budget, self.customer_budget, D('1000.00'),
                        staff_member)

        self.orders_budget = Budget.objects.create(
            name="Orders")

        facade.transfer(self.customer_budget, self.orders_budget, D('300.00'),
                        customer)

    def test_creates_four_transactions(self):
        self.assertEqual(4, Transaction.objects.all().count())
