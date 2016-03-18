from django.core.management.base import BaseCommand

from oscar_accounts.setup import create_default_accounts


class Command(BaseCommand):
    help = "Initialize oscar accounts default structure"

    def handle(self, *args, **options):
        create_default_accounts()
