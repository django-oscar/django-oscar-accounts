from decimal import Decimal as D
import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import G

from budgets import exceptions
from budgets.models import Budget, Transaction, BudgetTransaction


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
            self.assertFalse(self.budget.is_debit_permitted(amt))


class TestAnUnlimitedCreditLimitBudget(TestCase):

    def setUp(self):
        self.budget = Budget.objects.create(
            credit_limit=None)

    def test_permits_any_debit(self):
        for amt in (D('0.00'), D('1.00'), D('1000000')):
            self.assertTrue(self.budget.is_debit_permitted(amt))


class TestATransaction(TestCase):

    def setUp(self):
        self.user = G(User)

    def test_creates_2_budget_transactions(self):
        source = Budget.objects.create(credit_limit=None)
        destination = Budget.objects.create()
        txn = Transaction.objects.create(source, destination,
                                         D('10.00'), self.user)
        self.assertEqual(2, txn.budget_transactions.all().count())

    def test_raises_an_exception_when_trying_to_exceed_credit_limit_of_source(self):
        source = Budget.objects.create(credit_limit=D('10.00'))
        destination = Budget.objects.create()
        with self.assertRaises(exceptions.InsufficientBudget):
            Transaction.objects.create(source, destination,
                                       D('20.00'), self.user)

    def test_raises_an_exception_when_trying_to_debit_negative_value(self):
        source = Budget.objects.create(credit_limit=None)
        destination = Budget.objects.create()
        with self.assertRaises(exceptions.InvalidAmount):
            Transaction.objects.create(source, destination,
                                       D('-20.00'), self.user)

    def test_raises_an_exception_when_trying_to_use_inactive_source(self):
        today = datetime.date.today()
        source = Budget.objects.create(credit_limit=None,
            end_date=today - datetime.timedelta(days=1))
        destination = Budget.objects.create()
        with self.assertRaises(exceptions.InactiveBudget):
            Transaction.objects.create(source, destination,
                                       D('20.00'), self.user)

    def test_raises_an_exception_when_trying_to_use_inactive_destination(self):
        today = datetime.date.today()
        source = Budget.objects.create(credit_limit=None)
        destination = Budget.objects.create(
            end_date=today - datetime.timedelta(days=1))
        with self.assertRaises(exceptions.InactiveBudget):
            Transaction.objects.create(source, destination,
                                       D('20.00'), self.user)

    def test_cannot_be_deleted(self):
        source = Budget.objects.create(credit_limit=None)
        destination = Budget.objects.create()
        txn = Transaction.objects.create(source, destination,
                                         D('20.00'), self.user)
        with self.assertRaises(RuntimeError):
            txn.delete()

    def test_records_static_user_information_in_case_user_is_deleted(self):
        user = G(User, username="barry")
        source = Budget.objects.create(credit_limit=None)
        destination = Budget.objects.create()
        txn = Transaction.objects.create(source, destination,
                                   D('20.00'), user)
        self.assertEqual('barry', txn.authorisor_username)
        user.delete()
        txn = Transaction.objects.get(id=txn.id)
        self.assertEqual('barry', txn.authorisor_username)


class TestABudgetTransaction(TestCase):

    def test_cannot_be_deleted(self):
        budget_txn = G(BudgetTransaction)
        with self.assertRaises(RuntimeError):
            budget_txn.delete()

    def test_is_not_deleted_when_the_authorisor_is_deleted(self):
        user = G(User)
        source = Budget.objects.create(credit_limit=None)
        destination = Budget.objects.create()
        txn = Transaction.objects.create(source, destination,
                                   D('20.00'), user)
        self.assertEqual(2, txn.budget_transactions.all().count())
        user.delete()
        self.assertEqual(2, txn.budget_transactions.all().count())
