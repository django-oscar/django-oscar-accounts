from decimal import Decimal as D
import datetime

from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models import Sum

from django_dynamic_fixture import G

from budgets.models import Budget, Transaction
from budgets import facade
from budgets import exceptions


class TestANewZeroCreditLimitBudget(TestCase):

    def setUp(self):
        self.budget = Budget.objects.create()

    def test_defaults_to_zero_credit_limit(self):
        self.assertEqual(D('0.00'), self.budget.credit_limit)

    def test_does_not_permit_any_debits(self):
        self.assertFalse(self.budget.is_debit_permitted(D('1.00')))

    def test_has_zero_balance(self):
        self.assertEqual(D('0.00'), self.budget.balance())


class TestAFixedCreditLimitBudget(TestCase):

    def setUp(self):
        self.budget = Budget.objects.create(
            credit_limit=D('500'))

    def test_permits_smaller_and_equal_debits(self):
        for amt in (D('0.00'), D('1.00'), D('500')):
            self.assertTrue(self.budget.is_debit_permitted(amt))

    def test_does_not_permit_larger_amounts(self):
        for amt in (D('501'), D('1000')):
            self.assertTrue(self.budget.is_debit_permitted(amt))


class TestAnUnlimitedCreditLimitBudget(TestCase):

    def setUp(self):
        self.budget = Budget.objects.create(
            credit_limit=None)

    def test_permits_any_debit(self):
        for amt in (D('0.00'), D('1.00'), D('1000000')):
            self.assertTrue(self.budget.is_debit_permitted(amt))


class TestABudget(TestCase):

    def setUp(self):
        self.budget = Budget.objects.create()

    def test_defaults_to_being_active(self):
        self.assertTrue(self.budget.is_active())

    def test_raises_an_exception_when_trying_to_exceed_credit_limit(self):
        with self.assertRaises(exceptions.InsufficientBudget):
            self.budget._debit(D('10.00'))

    def test_raises_an_exception_when_trying_to_debit_negative_value(self):
        with self.assertRaises(exceptions.InvalidAmount):
            self.budget._debit(D('-10.00'))

    def test_raises_an_exception_when_trying_to_credit_negative_value(self):
        with self.assertRaises(exceptions.InvalidAmount):
            self.budget._credit(D('-10.00'))


class TestAnInactiveBudget(TestCase):

    def setUp(self):
        today = datetime.date.today()
        self.budget = Budget.objects.create(
            end_date=today - datetime.timedelta(days=1))

    def test_raises_an_exception_when_trying_to_debit(self):
        with self.assertRaises(exceptions.InactiveBudget):
            self.budget._debit(D('1.00'))

    def test_raises_an_exception_when_trying_to_credit(self):
        with self.assertRaises(exceptions.InactiveBudget):
            self.budget._credit(D('1.00'))


class TestATransferFromCompanyBudgetToCustomer(TestCase):

    def setUp(self):
        staff_member = G(User, is_staff=True)
        self.source = Budget.objects.create(
            credit_limit=None,
            name="Company")

        customer = G(User, is_staff=False)
        self.destination = Budget.objects.create(
            primary_user=customer)

        facade.transfer(self.source, self.destination, D('100.00'))

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
