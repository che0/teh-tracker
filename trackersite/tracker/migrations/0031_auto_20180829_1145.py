# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0030_auto_20180826_1941'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subtopic',
            options={'ordering': ['name'], 'verbose_name': 'Subtopic', 'verbose_name_plural': 'Subtopics'},
        ),
        migrations.AlterField(
            model_name='ticket',
            name='subtopic',
            field=models.ForeignKey(blank=True, to='tracker.Subtopic', help_text="Subtopic this ticket belongs to (if you don't know, leave this empty)", null=True, verbose_name='subtopic'),
        ),
    ]
