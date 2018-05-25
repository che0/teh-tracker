# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tracker', '0012_auto_20180430_1141'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('notification_type', models.CharField(max_length=20, null=True, verbose_name='type', choices=[(b'ack', 'ack'), (b'ticket', 'ticket')])),
                ('ack', models.ForeignKey(to='tracker.TicketAck', null=True)),
                ('target_user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('ticket', models.ForeignKey(to='tracker.Ticket', null=True)),
            ],
        ),
    ]
