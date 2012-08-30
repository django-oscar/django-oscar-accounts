from decimal import Decimal as D
import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import G

from budgets import exceptions
from budgets.models import Budget


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
        self.user = G(User)

    def test_defaults_to_being_active(self):
        self.assertTrue(self.budget.is_active())

    def test_raises_an_exception_when_trying_to_exceed_credit_limit(self):
        with self.assertRaises(exceptions.InsufficientBudget):
            self.budget._debit(1, D('10.00'), self.user)

    def test_raises_an_exception_when_trying_to_debit_negative_value(self):
        with self.assertRaises(exceptions.InvalidAmount):
            self.budget._debit(1, D('-10.00'), self.user)

    def test_raises_an_exception_when_trying_to_credit_negative_value(self):
        with self.assertRaises(exceptions.InvalidAmount):
            self.budget._credit(1, D('-10.00'), self.user)


class TestAnInactiveBudget(TestCase):

    def setUp(self):
        today = datetime.date.today()
        self.budget = Budget.objects.create(
            end_date=today - datetime.timedelta(days=1))
        self.user = G(User)

    def test_raises_an_exception_when_trying_to_debit(self):
        with self.assertRaises(exceptions.InactiveBudget):
            self.budget._debit(1, D('1.00'), self.user)

    def test_raises_an_exception_when_trying_to_credit(self):
        with self.assertRaises(exceptions.InactiveBudget):
            self.budget._credit(1, D('1.00'), self.user)
