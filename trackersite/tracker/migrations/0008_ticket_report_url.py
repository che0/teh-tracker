# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0007_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='report_url',
            field=models.CharField(default=b'', help_text='URL to your report, if you want to report something (or if your report is mandatory per topic administrator).', max_length=255, verbose_name='report url', blank=True),
        ),
    ]
