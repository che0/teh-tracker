# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0029_auto_20180826_1924'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='subtopic',
            field=models.ForeignKey(blank=True, to='tracker.Subtopic', help_text="Subtopic this ticket belongs to (if you don't know, leave this empty)", null=True, verbose_name='subtopics'),
        ),
    ]
