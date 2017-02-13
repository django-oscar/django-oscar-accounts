import uuid
import os.path

from django.conf import global_settings, settings
from oscar import OSCAR_MAIN_TEMPLATE_DIR, get_core_apps
from oscar.defaults import *  # noqa

from oscar_accounts import TEMPLATE_DIR as ACCOUNTS_TEMPLATE_DIR

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

SECRET_KEY = str(uuid.uuid4())

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.flatpages',
    'oscar_accounts',
    'widget_tweaks',
] + get_core_apps()

MIDDLEWARE_CLASSES = global_settings.MIDDLEWARE_CLASSES + [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'oscar.apps.basket.middleware.BasketMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            OSCAR_MAIN_TEMPLATE_DIR,
            os.path.join(OSCAR_MAIN_TEMPLATE_DIR, 'templates'),
            ACCOUNTS_TEMPLATE_DIR,
            # Include sandbox templates as they patch from templates that
            # are in Oscar 0.4 but not 0.3
            'sandbox/templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',

                # Oscar specific
                'oscar.apps.search.context_processors.search_form',
                'oscar.apps.promotions.context_processors.promotions',
                'oscar.apps.checkout.context_processors.checkout',
                'oscar.core.context_processors.metadata',
            ],
        },
    },
]

DEBUG=False

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine'
    }
}

ROOT_URLCONF = 'tests.urls'

STATIC_URL = '/static/'

SITE_ID=1
ACCOUNTS_UNIT_NAME='Giftcard'
USE_TZ=True

DDF_FILL_NULLABLE_FIELDS=False
ACCOUNTS_DEFERRED_INCOME_ACCOUNT_TYPES=('Test accounts',)
