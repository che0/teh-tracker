# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0021_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticketwatcher',
            name='ack_type',
            field=models.CharField(max_length=50, null=True, verbose_name=b'ack_type', choices=[(b'user_precontent', 'presubmitted'), (b'precontent', 'preaccepted'), (b'user_content', 'submitted'), (b'content', 'accepted'), (b'user_docs', 'expense documents submitted'), (b'docs', 'expense documents filed'), (b'archive', 'archived'), (b'close', 'closed')]),
        ),
        migrations.AddField(
            model_name='topicwatcher',
            name='ack_type',
            field=models.CharField(max_length=50, null=True, verbose_name=b'ack_type', choices=[(b'user_precontent', 'presubmitted'), (b'precontent', 'preaccepted'), (b'user_content', 'submitted'), (b'content', 'accepted'), (b'user_docs', 'expense documents submitted'), (b'docs', 'expense documents filed'), (b'archive', 'archived'), (b'close', 'closed')]),
        ),
        migrations.AddField(
            model_name='trackerprofile',
            name='muted_notifications',
            field=models.CharField(max_length=300, verbose_name=b'Muted notifications', blank=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(max_length=50, null=True, verbose_name=b'notification_type', choices=[(b'comment', 'Comment added'), (b'supervisor_notes', 'Supervisor notes changed'), (b'ticket_new', 'New ticket was created'), (b'ack_add_user_precontent', 'Ack presubmitted added'), (b'ack_remove_user_precontent', 'Ack presubmitted removed'), (b'ack_add_precontent', 'Ack preaccepted added'), (b'ack_remove_precontent', 'Ack preaccepted removed'), (b'ack_add_user_content', 'Ack submitted added'), (b'ack_remove_user_content', 'Ack submitted removed'), (b'ack_add_content', 'Ack accepted added'), (b'ack_remove_content', 'Ack accepted removed'), (b'ack_add_user_docs', 'Ack expense documents submitted added'), (b'ack_remove_user_docs', 'Ack expense documents submitted removed'), (b'ack_add_docs', 'Ack expense documents filed added'), (b'ack_remove_docs', 'Ack expense documents filed removed'), (b'ack_add_archive', 'Ack archived added'), (b'ack_remove_archive', 'Ack archived removed'), (b'ack_add_close', 'Ack closed added'), (b'ack_remove_close', 'Ack closed removed')]),
        ),
        migrations.AlterField(
            model_name='ticketwatcher',
            name='notification_type',
            field=models.CharField(max_length=50, verbose_name=b'notification_type', choices=[(b'comment', 'Comment added'), (b'supervisor_notes', 'Supervisor notes changed'), (b'ticket_new', 'New ticket was created'), (b'ack_add_user_precontent', 'Ack presubmitted added'), (b'ack_remove_user_precontent', 'Ack presubmitted removed'), (b'ack_add_precontent', 'Ack preaccepted added'), (b'ack_remove_precontent', 'Ack preaccepted removed'), (b'ack_add_user_content', 'Ack submitted added'), (b'ack_remove_user_content', 'Ack submitted removed'), (b'ack_add_content', 'Ack accepted added'), (b'ack_remove_content', 'Ack accepted removed'), (b'ack_add_user_docs', 'Ack expense documents submitted added'), (b'ack_remove_user_docs', 'Ack expense documents submitted removed'), (b'ack_add_docs', 'Ack expense documents filed added'), (b'ack_remove_docs', 'Ack expense documents filed removed'), (b'ack_add_archive', 'Ack archived added'), (b'ack_remove_archive', 'Ack archived removed'), (b'ack_add_close', 'Ack closed added'), (b'ack_remove_close', 'Ack closed removed')]),
        ),
        migrations.AlterField(
            model_name='topicwatcher',
            name='notification_type',
            field=models.CharField(max_length=50, verbose_name=b'notification_type', choices=[(b'comment', 'Comment added'), (b'supervisor_notes', 'Supervisor notes changed'), (b'ticket_new', 'New ticket was created'), (b'ack_add_user_precontent', 'Ack presubmitted added'), (b'ack_remove_user_precontent', 'Ack presubmitted removed'), (b'ack_add_precontent', 'Ack preaccepted added'), (b'ack_remove_precontent', 'Ack preaccepted removed'), (b'ack_add_user_content', 'Ack submitted added'), (b'ack_remove_user_content', 'Ack submitted removed'), (b'ack_add_content', 'Ack accepted added'), (b'ack_remove_content', 'Ack accepted removed'), (b'ack_add_user_docs', 'Ack expense documents submitted added'), (b'ack_remove_user_docs', 'Ack expense documents submitted removed'), (b'ack_add_docs', 'Ack expense documents filed added'), (b'ack_remove_docs', 'Ack expense documents filed removed'), (b'ack_add_archive', 'Ack archived added'), (b'ack_remove_archive', 'Ack archived removed'), (b'ack_add_close', 'Ack closed added'), (b'ack_remove_close', 'Ack closed removed')]),
        ),
    ]
