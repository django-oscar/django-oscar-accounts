from decimal import Decimal as D

from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models import Sum

from django_dynamic_fixture import G

from budgets.models import Budget, Transaction
from budgets import facade


class TestATransferFromCompanyBudgetToCustomer(TestCase):

    def setUp(self):
        staff_member = G(User, is_staff=True)
        source = Budget.objects.create(
            name="Company")

        customer = G(User, is_staff=False)
        destination = Budget.objects.create(
            primary_user=customer)

        facade.transfer(source, destination, D('100.00'))

        self.assertEqual(2, Transaction.objects.all().count())

    def test_creates_two_transactions(self):
        self.assertEqual(2, Transaction.objects.all().count())

    def test_preserves_zero_sum_invariant(self):
        aggregates = Transaction.objects.aggregate(sum=Sum('amount'))
        self.assertEqual(D('0.00'), aggregates['sum'])
