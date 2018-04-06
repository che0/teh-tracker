# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0008_ticket_report_url'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticket',
            name='custom_state',
        ),
    ]
