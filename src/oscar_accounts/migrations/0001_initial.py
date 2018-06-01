# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offer', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128, unique=True, null=True, blank=True)),
                ('description', models.TextField(help_text='This text is shown to customers during checkout', null=True, blank=True)),
                ('code', models.CharField(max_length=128, unique=True, null=True, blank=True)),
                ('status', models.CharField(default='Open', max_length=32)),
                ('credit_limit', models.DecimalField(default=Decimal('0.00'), null=True, max_digits=12, decimal_places=2, blank=True)),
                ('balance', models.DecimalField(default=Decimal('0.00'), null=True, max_digits=12, decimal_places=2)),
                ('start_date', models.DateTimeField(null=True, blank=True)),
                ('end_date', models.DateTimeField(null=True, blank=True)),
                ('can_be_used_for_non_products', models.BooleanField(default=True, help_text='Whether this account can be used to pay for shipping and other charges')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AccountType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', models.CharField(unique=True, max_length=255)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('code', models.CharField(max_length=128, unique=True, null=True, blank=True)),
                ('name', models.CharField(max_length=128)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IPAddressRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ip_address', models.IPAddressField(unique=True, verbose_name='IP address')),
                ('total_failures', models.PositiveIntegerField(default=0)),
                ('consecutive_failures', models.PositiveIntegerField(default=0)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_last_failure', models.DateTimeField(null=True)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'IP address record',
                'verbose_name_plural': 'IP address records',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.DecimalField(max_digits=12, decimal_places=2)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('account', models.ForeignKey(on_delete=models.CASCADE, related_name='transactions', to='oscar_accounts.Account')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Transfer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reference', models.CharField(max_length=64, unique=True, null=True)),
                ('amount', models.DecimalField(max_digits=12, decimal_places=2)),
                ('merchant_reference', models.CharField(max_length=128, null=True)),
                ('description', models.CharField(max_length=256, null=True)),
                ('username', models.CharField(max_length=128)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('destination', models.ForeignKey(on_delete=models.CASCADE, related_name='destination_transfers', to='oscar_accounts.Account')),
                ('parent', models.ForeignKey(on_delete=models.CASCADE, related_name='related_transfers', to='oscar_accounts.Transfer', null=True)),
                ('source', models.ForeignKey(on_delete=models.CASCADE, related_name='source_transfers', to='oscar_accounts.Account')),
                ('user', models.ForeignKey(related_name='transfers', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-date_created',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='transaction',
            name='transfer',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='transactions', to='oscar_accounts.Transfer'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='transaction',
            unique_together=set([('transfer', 'account')]),
        ),
        migrations.AddField(
            model_name='account',
            name='account_type',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='accounts', to='oscar_accounts.AccountType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='account',
            name='primary_user',
            field=models.ForeignKey(related_name='accounts', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='account',
            name='product_range',
            field=models.ForeignKey(on_delete=models.CASCADE, blank=True, to='offer.Range', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='account',
            name='secondary_users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
    ]
