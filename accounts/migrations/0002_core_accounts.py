# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from accounts import names


def create_core_accounts(apps, schema_editor):
    # Create asset accounts

    # We can't use the treebeard methods here, so these are translated to plain
    # model / manager methods.

    AccountType = apps.get_model('accounts', 'AccountType')

    # assets = AccountType.add_root(name=names.ASSETS)
    assets = AccountType.objects.create(
        path='0001', depth=1, name=names.ASSETS)

    # sales = assets.add_child(name=names.SALES)
    sales = AccountType.objects.create(
        path='00010001', depth=2, name=names.SALES)
    assets.numchild = 1
    assets.save()

    Account = apps.get_model('accounts', 'Account')

    # sales.accounts.create(name=names.REDEMPTIONS)
    Account.objects.create(account_type=sales, name=names.REDEMPTIONS)

    # sales.accounts.create(name=names.LAPSED)
    Account.objects.create(account_type=sales, name=names.LAPSED)

    # cash = assets.add_child(name=names.CASH)
    cash = AccountType.objects.create(
        path='00010002', depth=2, name=names.CASH)
    assets.numchild = 2
    assets.save()

    # cash.accounts.create(name=names.BANK, credit_limit=None)
    Account.objects.create(
        account_type=cash, name=names.BANK, credit_limit=None)

    # unpaid = assets.add_child(name=names.UNPAID_ACCOUNT_TYPE)
    unpaid = AccountType.objects.create(
        path='00010003', depth=2, name=names.UNPAID_ACCOUNT_TYPE)
    assets.numchild = 3
    assets.save()

    for name in names.UNPAID_ACCOUNTS:
        # unpaid.accounts.create(name=name, credit_limit=None)
        Account.objects.create(
            account_type=unpaid, name=name, credit_limit=None)

    # Create liability accounts

    # liabilities = AccountType.add_root(name=names.LIABILITIES)
    liabilities = AccountType.objects.create(
        path='0002', depth=1, name=names.LIABILITIES)

    # income = liabilities.add_child(name=names.DEFERRED_INCOME)
    income = AccountType.objects.create(
        path='00020001', depth=2, name=names.DEFERRED_INCOME)
    liabilities.numchild = 1
    liabilities.save()

    for i, name in enumerate(names.DEFERRED_INCOME_ACCOUNT_TYPES):
        # income.add_child(name=name)
        AccountType.objects.create(
            path='00020001{:0=4}'.format(i + 1), depth=3, name=name)
        income.numchild = income.numchild + 1
        income.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_core_accounts)
    ]
