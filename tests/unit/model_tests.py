from decimal import Decimal as D
import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import G

from accounts import exceptions
from accounts.models import Account, Transfer, Transaction


class TestAnAccount(TestCase):

    def setUp(self):
        self.account = Account()

    def test_is_open_by_default(self):
        self.assertEqual(Account.OPEN, self.account.status)

    def test_can_be_closed(self):
        self.account.close()
        self.assertEqual(Account.CLOSED, self.account.status)


class TestAnAccountWithFunds(TestCase):

    def setUp(self):
        self.account = Account()
        self.account.balance = D('100.00')

    def test_cannot_be_closed(self):
        with self.assertRaises(exceptions.AccountNotEmpty):
            self.account.close()


class TestANewZeroCreditLimitAccount(TestCase):

    def setUp(self):
        self.account = Account.objects.create()

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
        self.account = Account.objects.create(
            credit_limit=D('500'))

    def test_permits_smaller_and_equal_debits(self):
        for amt in (D('0.00'), D('1.00'), D('500')):
            self.assertTrue(self.account.is_debit_permitted(amt))

    def test_does_not_permit_larger_amounts(self):
        for amt in (D('501'), D('1000')):
            self.assertFalse(self.account.is_debit_permitted(amt))


class TestAnUnlimitedCreditLimitAccount(TestCase):

    def setUp(self):
        self.account = Account.objects.create(
            credit_limit=None)

    def test_permits_any_debit(self):
        for amt in (D('0.00'), D('1.00'), D('1000000')):
            self.assertTrue(self.account.is_debit_permitted(amt))


class TestAccountManager(TestCase):

    def test_has_expired_filter(self):
        today = datetime.date.today()
        Account.objects.create(end_date=today - datetime.timedelta(days=1))
        accounts = Account.expired.all()
        self.assertEqual(1, accounts.count())


class TestATransfer(TestCase):

    def setUp(self):
        self.user = G(User)

    def test_creates_2_transactions(self):
        source = Account.objects.create(credit_limit=None)
        destination = Account.objects.create()
        transfer = Transfer.objects.create(source, destination,
                                      D('10.00'), self.user)
        self.assertEqual(2, transfer.transactions.all().count())

    def test_raises_an_exception_when_trying_to_exceed_credit_limit_of_source(self):
        source = Account.objects.create(credit_limit=D('10.00'))
        destination = Account.objects.create()
        with self.assertRaises(exceptions.InsufficientFunds):
            Transfer.objects.create(source, destination,
                                    D('20.00'), self.user)

    def test_raises_an_exception_when_trying_to_debit_negative_value(self):
        source = Account.objects.create(credit_limit=None)
        destination = Account.objects.create()
        with self.assertRaises(exceptions.InvalidAmount):
            Transfer.objects.create(source, destination,
                                    D('-20.00'), self.user)

    def test_raises_an_exception_when_trying_to_use_inactive_source(self):
        today = datetime.date.today()
        source = Account.objects.create(credit_limit=None,
            end_date=today - datetime.timedelta(days=1))
        destination = Account.objects.create()
        with self.assertRaises(exceptions.InactiveAccount):
            Transfer.objects.create(source, destination,
                                    D('20.00'), self.user)

    def test_raises_an_exception_when_trying_to_use_inactive_destination(self):
        today = datetime.date.today()
        source = Account.objects.create(credit_limit=None)
        destination = Account.objects.create(
            end_date=today - datetime.timedelta(days=1))
        with self.assertRaises(exceptions.InactiveAccount):
            Transfer.objects.create(source, destination,
                                    D('20.00'), self.user)

    def test_raises_an_exception_when_trying_to_use_closed_source(self):
        source = Account.objects.create(credit_limit=None)
        source.close()
        destination = Account.objects.create()
        with self.assertRaises(exceptions.ClosedAccount):
            Transfer.objects.create(source, destination,
                                       D('20.00'), self.user)

    def test_raises_an_exception_when_trying_to_use_closed_destination(self):
        source = Account.objects.create(credit_limit=None)
        destination = Account.objects.create()
        destination.close()
        with self.assertRaises(exceptions.ClosedAccount):
            Transfer.objects.create(source, destination,
                                    D('20.00'), self.user)

    def test_cannot_be_deleted(self):
        source = Account.objects.create(credit_limit=None)
        destination = Account.objects.create()
        transfer = Transfer.objects.create(source, destination,
                                           D('20.00'), self.user)
        with self.assertRaises(RuntimeError):
            transfer.delete()

    def test_records_static_user_information_in_case_user_is_deleted(self):
        user = G(User, username="barry")
        source = Account.objects.create(credit_limit=None)
        destination = Account.objects.create()
        transfer = Transfer.objects.create(source, destination,
                                           D('20.00'), user)
        self.assertEqual('barry', transfer.authorisor_username)
        user.delete()
        transfer = Transfer.objects.get(id=transfer.id)
        self.assertEqual('barry', transfer.authorisor_username)


class TestATransaction(TestCase):

    def test_cannot_be_deleted(self):
        txn = G(Transaction)
        with self.assertRaises(RuntimeError):
            txn.delete()

    def test_is_not_deleted_when_the_authorisor_is_deleted(self):
        user = G(User)
        source = Account.objects.create(credit_limit=None)
        destination = Account.objects.create()
        txn = Transfer.objects.create(source, destination,
                                      D('20.00'), user)
        self.assertEqual(2, txn.transactions.all().count())
        user.delete()
        self.assertEqual(2, txn.transactions.all().count())
