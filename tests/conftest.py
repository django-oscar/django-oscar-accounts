import os
import django

import pytest
from oscar_accounts import setup



# It should be possible to just set DJANGO_SETTINGS_MODULE in setup.cfg
# or pytest.ini, but it doesn't work because pytest tries to do some
# magic by detecting a manage.py (which we don't have for our test suite).
# So we need to go the manual route here.
def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
    django.setup()


@pytest.fixture
def default_accounts():
    setup.create_default_accounts()
