# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0025_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticket',
            name='tags',
        ),
        migrations.AddField(
            model_name='ticket',
            name='tag',
            field=models.ForeignKey(blank=True, to='tracker.Tag', help_text='Tag this ticket belongs to', null=True, verbose_name='tags'),
        ),
    ]
