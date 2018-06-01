import os.path
import uuid

from oscar import OSCAR_MAIN_TEMPLATE_DIR, get_core_apps
from oscar.defaults import *  # noqa F401

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

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'oscar.apps.basket.middleware.BasketMiddleware',
]

DEBUG = False

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine'
    }
}

ROOT_URLCONF = 'tests.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(OSCAR_MAIN_TEMPLATE_DIR, 'templates'),
            OSCAR_MAIN_TEMPLATE_DIR,
            ACCOUNTS_TEMPLATE_DIR,
        ],
        'OPTIONS': {
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',

                'oscar.apps.search.context_processors.search_form',
                'oscar.apps.promotions.context_processors.promotions',
                'oscar.apps.checkout.context_processors.checkout',
                'oscar.core.context_processors.metadata',
            ],
        }
    }
]

STATIC_URL = '/static/'

SITE_ID = 1
ACCOUNTS_UNIT_NAME = 'Giftcard'
USE_TZ = True

DDF_FILL_NULLABLE_FIELDS = False
ACCOUNTS_DEFERRED_INCOME_ACCOUNT_TYPES = ('Test accounts',)
