from django.db.models.signals import post_syncdb
from django.conf import settings

from accounts import models


def ensure_core_accounts_exists(sender, **kwargs):
    create_source_account()
    create_sales_account()
    create_expired_account()


def create_sales_account():
    name = getattr(settings, 'ACCOUNTS_SALES_NAME')
    models.Account.objects.get_or_create(name=name)


def create_expired_account():
    name = getattr(settings, 'ACCOUNTS_EXPIRED_NAME')
    models.Account.objects.get_or_create(name=name)


def create_source_account():
    # Create a source account if one does not exist
    if not hasattr(settings, 'ACCOUNTS_SOURCE_NAME'):
        return
    # We only create the source account if there are no accounts already
    # created.
    if models.Account.objects.all().count() > 0:
        return
    name = getattr(settings, 'ACCOUNTS_SOURCE_NAME')
    models.Account.objects.get_or_create(name=name, credit_limit=None)


post_syncdb.connect(ensure_core_accounts_exists, sender=models)
