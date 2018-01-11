# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0004_auto_20171002_2125'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticketack',
            name='comment',
            field=models.CharField(max_length=255, verbose_name='comment', blank=True),
        ),
    ]
