from django.db.models.signals import post_syncdb
from django.conf import settings

from accounts import models


def ensure_core_accounts_exists(sender, **kwargs):
    create_source_account()
    create_sales_account()
    create_expired_account()


def create_sales_account():
    name = getattr(settings, 'ACCOUNTS_SALES_NAME')
    __, created = models.Account.objects.get_or_create(name=name)
    if created:
        print "Created sales account '%s'" % name


def create_expired_account():
    name = getattr(settings, 'ACCOUNTS_EXPIRED_NAME')
    __, created = models.Account.objects.get_or_create(name=name)
    if created:
        print "Created expired account '%s'" % name


def create_source_account():
    # Create a source account if one does not exist
    if not hasattr(settings, 'ACCOUNTS_SOURCE_NAME'):
        return
    # We only create the source account if there are no accounts already
    # created.
    if models.Account.objects.all().count() > 0:
        return
    name = getattr(settings, 'ACCOUNTS_SOURCE_NAME')
    __, created = models.Account.objects.get_or_create(name=name,
                                                       credit_limit=None)
    if created:
        print "Created source account '%s'" % name


post_syncdb.connect(ensure_core_accounts_exists, sender=models)
