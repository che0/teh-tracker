# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0009_remove_ticket_custom_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='custom_state',
            field=models.CharField(help_text='Custom state description', max_length=100, verbose_name='custom state', blank=True),
        ),
    ]
