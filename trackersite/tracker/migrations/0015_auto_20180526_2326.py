# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0014_notification_comment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(max_length=20, null=True, verbose_name='type', choices=[(b'ack', b'ack'), (b'comment', b'comment'), (b'ticket_new', b'ticket_new')]),
        ),
    ]
