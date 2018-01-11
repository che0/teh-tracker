# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tracker.models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0003_ticket_event_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='rating_percentage',
            field=tracker.models.PercentageField(default=100, help_text='Rating percentage set by topic administrator', null=True, verbose_name='rating percentage', blank=True),
        ),
    ]
