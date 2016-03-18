import datetime
from decimal import Decimal as D

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from oscar.test.factories import UserFactory

from oscar_accounts import exceptions
from oscar_accounts.models import Account, Transaction, Transfer
from oscar_accounts.test_factories import AccountFactory, TransactionFactory


class TestAnAccount(TestCase):

    def setUp(self):
        self.account = Account()

    def test_is_open_by_default(self):
        self.assertEqual(Account.OPEN, self.account.status)

    def test_can_be_closed(self):
        self.account.close()
        self.assertEqual(Account.CLOSED, self.account.status)

    def test_always_saves_the_code_as_uppercase(self):
        self.account.code = 'abc'
        self.account.save()
        self.assertEquals('ABC', self.account.code)

    def test_can_be_authorised_when_no_user_passed(self):
        self.assertTrue(self.account.can_be_authorised_by())

    def test_can_be_authorised_by_anyone_by_default(self):
        self.account.save()
        user = UserFactory()
        self.assertTrue(self.account.can_be_authorised_by(user))

    def test_can_only_be_authorised_by_primary_user_when_set(self):
        primary = UserFactory()
        other = UserFactory()
        self.account.primary_user = primary
        self.account.save()

        self.assertTrue(self.account.can_be_authorised_by(primary))
        self.assertFalse(self.account.can_be_authorised_by(other))

    def test_can_only_be_authorised_by_secondary_users_when_set(self):
        self.account.save()
        users = [UserFactory(), UserFactory()]
        other = UserFactory()
        for user in users:
            self.account.secondary_users.add(user)

        for user in users:
            self.assertTrue(self.account.can_be_authorised_by(user))
        self.assertFalse(self.account.can_be_authorised_by(other))

    def test_does_not_permit_an_allocation(self):
        amt = self.account.permitted_allocation(
            None, D('2.00'), D('12.00'))
        self.assertEqual(D('0.00'), amt)


class TestAnAccountWithFunds(TestCase):

    def setUp(self):
        self.account = Account()
        self.account.balance = D('100.00')

    def test_cannot_be_closed(self):
        with self.assertRaises(exceptions.AccountNotEmpty):
            self.account.close()

    def test_allows_allocations_less_than_balance(self):
        amt = self.account.permitted_allocation(
            None, D('2.00'), D('12.00'))
        self.assertEqual(D('12.00'), amt)

    def test_doesnt_allow_allocations_greater_than_balance(self):
        amt = self.account.permitted_allocation(
            None, D('2.00'), D('120.00'))
        self.assertEqual(D('100.00'), amt)


class TestAnAccountWithFundsButOnlyForProducts(TestCase):

    def setUp(self):
        self.account = Account()
        self.account.can_be_used_for_non_products = False
        self.account.balance = D('100.00')

    def test_doesnt_allow_shipping_in_allocation(self):
        amt = self.account.permitted_allocation(
            None, D('20.00'), D('40.00'))
        self.assertEqual(D('20.00'), amt)


class TestANewZeroCreditLimitAccount(TestCase):

    def setUp(self):
        self.account = Account()

    def test_defaults_to_zero_credit_limit(self):
        self.assertEqual(D('0.00'), self.account.credit_limit)

    def test_does_not_permit_any_debits(self):
        self.assertFalse(self.account.is_debit_permitted(D('1.00')))

    def test_has_zero_balance(self):
        self.assertEqual(D('0.00'), self.account.balance)

    def test_has_zero_transactions(self):
        self.assertEqual(0, self.account.num_transactions())


class TestAFixedCreditLimitAccount(TestCase):

    def setUp(self):
        self.account = AccountFactory(
            credit_limit=D('500'), start_date=None, end_date=None)

    def test_permits_smaller_and_equal_debits(self):
        for amt in (D('0.00'), D('1.00'), D('500')):
            self.assertTrue(self.account.is_debit_permitted(amt))

    def test_does_not_permit_larger_amounts(self):
        for amt in (D('501'), D('1000')):
            self.assertFalse(self.account.is_debit_permitted(amt))


class TestAnUnlimitedCreditLimitAccount(TestCase):

    def setUp(self):
        self.account = AccountFactory(
            credit_limit=None, start_date=None, end_date=None)

    def test_permits_any_debit(self):
        for amt in (D('0.00'), D('1.00'), D('1000000')):
            self.assertTrue(self.account.is_debit_permitted(amt))


class TestAccountExpiredManager(TestCase):

    def test_includes_only_expired_accounts(self):
        now = timezone.now()
        AccountFactory(end_date=now - datetime.timedelta(days=1))
        AccountFactory(end_date=now + datetime.timedelta(days=1))
        accounts = Account.expired.all()
        self.assertEqual(1, accounts.count())


class TestAccountActiveManager(TestCase):

    def test_includes_only_active_accounts(self):
        now = timezone.now()
        expired = AccountFactory(end_date=now - datetime.timedelta(days=1))
        AccountFactory(end_date=now + datetime.timedelta(days=1))
        AccountFactory(start_date=now, end_date=now + datetime.timedelta(days=1))
        accounts = Account.active.all()
        self.assertTrue(expired not in accounts)


class TestATransaction(TestCase):

    def test_cannot_be_deleted(self):
        txn = TransactionFactory()
        with self.assertRaises(RuntimeError):
            txn.delete()

    def test_is_not_deleted_when_the_authorisor_is_deleted(self):
        user = UserFactory()
        source = AccountFactory(credit_limit=None, primary_user=user, start_date=None, end_date=None)
        destination = AccountFactory(start_date=None, end_date=None)
        txn = Transfer.objects.create(source, destination,
                                      D('20.00'), user=user)
        self.assertEqual(2, txn.transactions.all().count())
        user.delete()
        self.assertEqual(2, txn.transactions.all().count())
