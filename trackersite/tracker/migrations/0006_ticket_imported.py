# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0005_auto_20171221_1603'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='imported',
            field=models.BooleanField(default=False, help_text='Was this ticket imported from older Tracker version?', verbose_name='imported'),
        ),
    ]
