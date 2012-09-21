#!/usr/bin/env python
import sys
from coverage import coverage
from optparse import OptionParser

import logging
logging.disable(logging.CRITICAL)

from django.conf import settings

if not settings.configured:
    from oscar.defaults import *
    extra_settings = {}
    for key, value in locals().items():
        if key.startswith('OSCAR'):
            extra_settings[key] = value

    from oscar import get_core_apps, OSCAR_MAIN_TEMPLATE_DIR

    settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    }
                },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.admin',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.sites',
                'django.contrib.flatpages',
                'accounts',
                'south',
                ] + get_core_apps(),
            MIDDLEWARE_CLASSES=(
                'django.middleware.common.CommonMiddleware',
                'django.contrib.sessions.middleware.SessionMiddleware',
                'django.middleware.csrf.CsrfViewMiddleware',
                'django.contrib.auth.middleware.AuthenticationMiddleware',
                'django.contrib.messages.middleware.MessageMiddleware',
                'django.middleware.transaction.TransactionMiddleware',
                'oscar.apps.basket.middleware.BasketMiddleware',
            ),
            DEBUG=False,
            SOUTH_TESTS_MIGRATE=False,
            HAYSTACK_CONNECTIONS={
                'default': {
                    'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
                },
            },
            ROOT_URLCONF='tests.urls',
            TEMPLATE_DIRS=(OSCAR_MAIN_TEMPLATE_DIR,),
            SITE_ID=1,
            ACCOUNTS_UNIT_NAME='Giftcard',
            NOSE_ARGS=['-s', '--with-spec', '-x'],
            **extra_settings
        )

from django_nose import NoseTestSuiteRunner


def run_tests(*test_args):
    if 'south' in settings.INSTALLED_APPS:
        from south.management.commands import patch_for_test_db_setup
        patch_for_test_db_setup()

    if not test_args:
        test_args = ['tests']

    # Run tests
    test_runner = NoseTestSuiteRunner(verbosity=1)

    c = coverage(source=['accounts'], omit=['*migrations*', '*tests*'])
    c.start()
    num_failures = test_runner.run_tests(test_args)
    c.stop()

    if num_failures > 0:
        sys.exit(num_failures)
    print "Generating HTML coverage report"
    c.html_report()

def generate_migration():
    from south.management.commands.schemamigration import Command
    com = Command()
    com.handle(app='accounts', initial=True)


if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    run_tests(*args)
