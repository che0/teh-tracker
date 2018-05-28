# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0017_auto_20180528_1833'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(max_length=50, null=True, verbose_name=b'notification_type', choices=[(b'ack', b'ack'), (b'ack_remove', b'ack_remove'), (b'comment', b'comment'), (b'supervisor_notes', b'supervisor_notes'), (b'ticket_new', b'ticket_new')]),
        ),
    ]
