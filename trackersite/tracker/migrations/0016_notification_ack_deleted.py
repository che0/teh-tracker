# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0015_auto_20180526_2326'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='ack_deleted',
            field=models.CharField(max_length=1000, null=True, blank=True),
        ),
    ]
