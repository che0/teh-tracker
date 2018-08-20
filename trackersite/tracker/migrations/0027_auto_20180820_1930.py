# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0026_auto_20180621_1707'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='ticket',
            field=models.ForeignKey(to='tracker.Ticket', null=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(max_length=50, null=True, verbose_name=b'notification_type', choices=[(b'comment', 'Comment added'), (b'supervisor_notes', 'Supervisor notes changed'), (b'ticket_new', 'New ticket was created'), (b'ack_add', 'Ack added'), (b'ack_remove', 'Ack removed'), (b'preexpeditures_change', 'Preexpeditures changed'), (b'expeditures_change', 'Expeditures changed'), (b'media_change', 'Media changed')]),
        ),
        migrations.AlterField(
            model_name='ticketwatcher',
            name='notification_type',
            field=models.CharField(max_length=50, verbose_name=b'notification_type', choices=[(b'comment', 'Comment added'), (b'supervisor_notes', 'Supervisor notes changed'), (b'ticket_new', 'New ticket was created'), (b'ack_add', 'Ack added'), (b'ack_remove', 'Ack removed'), (b'preexpeditures_change', 'Preexpeditures changed'), (b'expeditures_change', 'Expeditures changed'), (b'media_change', 'Media changed')]),
        ),
        migrations.AlterField(
            model_name='topicwatcher',
            name='notification_type',
            field=models.CharField(max_length=50, verbose_name=b'notification_type', choices=[(b'comment', 'Comment added'), (b'supervisor_notes', 'Supervisor notes changed'), (b'ticket_new', 'New ticket was created'), (b'ack_add', 'Ack added'), (b'ack_remove', 'Ack removed'), (b'preexpeditures_change', 'Preexpeditures changed'), (b'expeditures_change', 'Expeditures changed'), (b'media_change', 'Media changed')]),
        ),
    ]
