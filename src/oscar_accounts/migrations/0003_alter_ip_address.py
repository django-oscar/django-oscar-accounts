# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oscar_accounts', '0002_core_accounts'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ipaddressrecord',
            name='ip_address',
            field=models.GenericIPAddressField(unique=True, verbose_name='IP address'),
        ),
    ]
