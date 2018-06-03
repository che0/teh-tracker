# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tracker', '0019_ticketwatcher'),
    ]

    operations = [
        migrations.CreateModel(
            name='TopicWatcher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('notification_type', models.CharField(max_length=50, verbose_name=b'notification_type', choices=[(b'ack', 'Ack added'), (b'ack_remove', 'Ack removed'), (b'comment', 'Comment added'), (b'supervisor_notes', 'Supervisor notes changed'), (b'ticket_new', 'New ticket was created')])),
                ('topic', models.ForeignKey(to='tracker.Topic')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(max_length=50, null=True, verbose_name=b'notification_type', choices=[(b'ack', 'Ack added'), (b'ack_remove', 'Ack removed'), (b'comment', 'Comment added'), (b'supervisor_notes', 'Supervisor notes changed'), (b'ticket_new', 'New ticket was created')]),
        ),
        migrations.AlterField(
            model_name='ticketwatcher',
            name='notification_type',
            field=models.CharField(max_length=50, verbose_name=b'notification_type', choices=[(b'ack', 'Ack added'), (b'ack_remove', 'Ack removed'), (b'comment', 'Comment added'), (b'supervisor_notes', 'Supervisor notes changed'), (b'ticket_new', 'New ticket was created')]),
        ),
    ]
