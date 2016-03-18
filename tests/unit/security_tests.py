from django.test import TestCase
from django.test.client import RequestFactory

from oscar_accounts import security


class TestBruteForceAPI(TestCase):
    """Brute force API"""

    def setUp(self):
        factory = RequestFactory()
        self.request = factory.post('/')

    def test_does_not_block_by_default(self):
        self.assertFalse(security.is_blocked(self.request))

    def test_blocks_after_freeze_threshold(self):
        for __ in range(3):
            security.record_failed_request(self.request)
        self.assertTrue(security.is_blocked(self.request))

    def test_resets_after_success(self):
        for __ in range(2):
            security.record_failed_request(self.request)
        security.record_successful_request(self.request)
        security.record_failed_request(self.request)
        self.assertFalse(security.is_blocked(self.request))
