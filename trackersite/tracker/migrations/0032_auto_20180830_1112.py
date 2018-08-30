# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0031_auto_20180829_1145'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='trackerprofile',
            options={'verbose_name': 'Tracker profile', 'verbose_name_plural': 'Tracker profiles'},
        ),
    ]
