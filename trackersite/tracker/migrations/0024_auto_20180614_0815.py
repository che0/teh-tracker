# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0023_auto_20180614_0759'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='tags',
            field=models.ManyToManyField(help_text='Tags this ticket belongs to', to='tracker.Tag', verbose_name='tags', blank=True),
        ),
    ]
