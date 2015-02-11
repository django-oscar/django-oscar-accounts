#!/usr/bin/env python
import sys
import os
from optparse import OptionParser

import logging
logging.disable(logging.CRITICAL)

from django.conf import settings, global_settings

if not settings.configured:
    from oscar.defaults import *  # noqa
    extra_settings = {k: v for k, v in locals().items() if k.startswith('OSCAR')}

    from oscar import get_core_apps, OSCAR_MAIN_TEMPLATE_DIR
    from accounts import TEMPLATE_DIR as ACCOUNTS_TEMPLATE_DIR

    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
            }
        },
        STATICFILES_FINDERS=(
            'django.contrib.staticfiles.finders.FileSystemFinder',
            'django.contrib.staticfiles.finders.AppDirectoriesFinder',
            'compressor.finders.CompressorFinder',
        ),
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.admin',
            'django.contrib.contenttypes',
            'django.contrib.staticfiles',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.flatpages',
            'accounts',
            'compressor',
        ] + get_core_apps(),
        MIDDLEWARE_CLASSES=global_settings.MIDDLEWARE_CLASSES + (
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'oscar.apps.basket.middleware.BasketMiddleware',
        ),
        TEMPLATE_CONTEXT_PROCESSORS=global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
            'django.core.context_processors.request',
            'oscar.apps.search.context_processors.search_form',
            'oscar.apps.promotions.context_processors.promotions',
            'oscar.apps.checkout.context_processors.checkout',
            'oscar.core.context_processors.metadata',
        ),
        DEBUG=False,
        HAYSTACK_CONNECTIONS={
            'default': {
                'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
            },
        },
        ROOT_URLCONF='tests.urls',
        TEMPLATE_DIRS=(
            OSCAR_MAIN_TEMPLATE_DIR,
            os.path.join(OSCAR_MAIN_TEMPLATE_DIR, 'templates'),
            ACCOUNTS_TEMPLATE_DIR,
            # Include sandbox templates as they patch from templates that
            # are in Oscar 0.4 but not 0.3
            'sandbox/templates',
        ),
        STATIC_URL='/static/',
        COMPRESS_ROOT='',
        COMPRESS_ENABLED=False,
        SITE_ID=1,
        ACCOUNTS_UNIT_NAME='Giftcard',
        NOSE_ARGS=['--nocapture', '--with-specplugin'],
        USE_TZ=True,
        DDF_FILL_NULLABLE_FIELDS=False,
        ACCOUNTS_DEFERRED_INCOME_ACCOUNT_TYPES=('Test accounts',),
        **extra_settings
    )

from django_nose import NoseTestSuiteRunner


def run_tests(*test_args):
    if not test_args:
        test_args = ['tests']

    # Run tests
    test_runner = NoseTestSuiteRunner(verbosity=1)
    num_failures = test_runner.run_tests(test_args)

    if num_failures > 0:
        sys.exit(num_failures)


if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()  # noqa
    run_tests(*args)
