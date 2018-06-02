# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tracker', '0018_auto_20180528_2003'),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketWatcher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('notification_type', models.CharField(max_length=50, verbose_name=b'notification_type', choices=[(b'ack', b'ack'), (b'ack_remove', b'ack_remove'), (b'comment', b'comment'), (b'supervisor_notes', b'supervisor_notes'), (b'ticket_new', b'ticket_new')])),
                ('ticket', models.ForeignKey(to='tracker.Ticket')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
