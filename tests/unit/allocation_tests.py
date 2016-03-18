from decimal import Decimal as D

from django.test import TestCase

from oscar_accounts.checkout.allocation import Allocations


class TestAllocations(TestCase):

    def setUp(self):
        self.allocations = Allocations()

    def test_have_default_total_of_zero(self):
        self.assertEqual(D('0.00'), self.allocations.total)

    def test_has_items_interface(self):
        self.allocations.add('A', D('10.00'))

        for code, amount in self.allocations.items():
            self.assertEqual('A', code)
            self.assertEqual(D('10.00'), amount)

    def test_allow_items_to_be_removed(self):
        self.allocations.add('A', D('10.00'))
        self.assertEqual(D('10.00'), self.allocations.total)
        self.allocations.remove('A')
        self.assertEqual(D('0.00'), self.allocations.total)
