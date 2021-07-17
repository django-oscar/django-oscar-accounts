import os
from decimal import Decimal as D

import oscar
from oscar.defaults import *    # noqa

PROJECT_DIR = os.path.dirname(__file__)
location = lambda x: os.path.join(os.path.dirname(os.path.realpath(__file__)), x)

DEBUG = True
SQL_DEBUG = True

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(__file__), 'db.sqlite'),
    }
}
ATOMIC_REQUESTS = True

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = location("assets")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
# ADMIN_MEDIA_PREFIX = '/media/admin/'

STATIC_URL = '/static/'
STATIC_ROOT = location("static")
STATICFILES_DIRS = ()
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '$)a7n&o80u!6y5t-+jrd3)3!%vh&shg$wqpjpxc!ar&p#!)n1a'

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'oscar.apps.basket.middleware.BasketMiddleware',
)

INTERNAL_IPS = ('127.0.0.1',)

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [location('templates')],
        'OPTIONS': {
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.request",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.contrib.messages.context_processors.messages",
                # Oscar specific
                'oscar.apps.search.context_processors.search_form',
                'oscar.apps.checkout.context_processors.checkout',
                'oscar.core.context_processors.metadata',
            ],
            'debug': DEBUG,
        }
    }
]

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'oscar.checkout': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'INFO',
        },
        'accounts': {
            'handlers': ['console'],
            'propagate': False,
            'level': 'DEBUG',
        },
    }
}


INSTALLED_APPS = [
    'oscar_accounts.apps.AccountsConfig',
    'oscar_accounts.dashboard.apps.AccountsDashboardConfig',
    'sorl.thumbnail',
] + oscar.INSTALLED_APPS

INSTALLED_APPS[INSTALLED_APPS.index('oscar.apps.shipping.apps.ShippingConfig')] = 'apps.shipping.apps.ShippingConfig'
INSTALLED_APPS[INSTALLED_APPS.index('oscar.apps.checkout.apps.CheckoutConfig')] = 'apps.checkout.apps.CheckoutConfig'

AUTHENTICATION_BACKENDS = (
    'oscar.apps.customer.auth_backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
)

LOGIN_REDIRECT_URL = '/accounts/'
APPEND_SLASH = True


OSCAR_SHOP_TAGLINE = "Accounts"

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    },
}

USE_TZ = True

# Accounts settings
# =================

OSCAR_DASHBOARD_NAVIGATION.append(      # noqa F405
    {
        'label': 'Accounts',
        'icon': 'fas fa-globe',
        'children': [
            {
                'label': 'Accounts',
                'url_name': 'accounts_dashboard:accounts-list',
            },
            {
                'label': 'Transfers',
                'url_name': 'accounts_dashboard:transfers-list',
            },
            {
                'label': 'Deferred income report',
                'url_name': 'accounts_dashboard:report-deferred-income',
            },
            {
                'label': 'Profit/loss report',
                'url_name': 'accounts_dashboard:report-profit-loss',
            },
        ]
    })

ACCOUNTS_UNIT_NAME = 'Giftcard'
ACCOUNTS_UNIT_NAME_PLURAL = 'Giftcards'
ACCOUNTS_MIN_LOAD_VALUE = D('30.00')
ACCOUNTS_MAX_ACCOUNT_VALUE = D('1000.00')

try:
    from settings_local import *        # noqa
except ImportError:
    pass
