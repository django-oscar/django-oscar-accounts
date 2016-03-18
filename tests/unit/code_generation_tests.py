import string

from django.test import TestCase

from oscar_accounts import codes


class TestCodeGeneration(TestCase):

    def test_create_codes_of_correct_length(self):
        for size in [4, 6, 8]:
            code = codes.generate(size=size)
            self.assertTrue(size, len(code))

    def test_create_codes_using_correct_default_character_set(self):
        code = codes.generate()
        chars = string.ascii_uppercase + string.digits
        for char in code:
            self.assertTrue(char in chars)

    def test_can_create_codes_using_custom_character_set(self):
        chars = string.ascii_uppercase
        code = codes.generate(chars=chars)
        for char in code:
            self.assertTrue(char in chars)
