# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0016_notification_ack_deleted'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notification',
            name='ack',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='ack_deleted',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='comment',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='ticket',
        ),
        migrations.AddField(
            model_name='notification',
            name='fired',
            field=models.DateTimeField(default=datetime.datetime(2018, 5, 28, 18, 33, 28, 559266), verbose_name=b'fired', auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='notification',
            name='text',
            field=models.TextField(default=b'', verbose_name=b'text'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(max_length=50, null=True, verbose_name=b'notification_type', choices=[(b'ack', b'ack'), (b'ack_remove', b'ack_remove'), (b'comment', b'comment'), (b'ticket_new', b'ticket_new')]),
        ),
    ]
