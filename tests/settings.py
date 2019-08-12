import uuid

import oscar
from oscar.defaults import *  # noqa F401

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
    'oscar_accounts.apps.AccountsConfig',
    'oscar_accounts.dashboard.apps.AccountsDashboardConfig',
    'oscar_accounts.api.apps.AccountsAPIConfig',
    'sorl.thumbnail',
] + oscar.INSTALLED_APPS

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
        'DIRS': [],
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
