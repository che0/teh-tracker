# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0002_auto_20170712_2108'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='event_url',
            field=models.URLField(help_text='Link to a public page describing the event, if it exist', verbose_name='event url', blank=True),
        ),
    ]
