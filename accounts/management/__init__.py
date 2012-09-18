from django.db.models.signals import post_syncdb
from django.conf import settings

from accounts import models


def ensure_source_account_exists(sender, **kwargs):
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


post_syncdb.connect(ensure_source_account_exists, sender=models)
