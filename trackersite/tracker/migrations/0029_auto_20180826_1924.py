# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0028_auto_20180820_2000'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subtopic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80, verbose_name='name')),
                ('description', models.TextField(help_text='Description shown to users who enter tickets for this subtopic', verbose_name='description', blank=True)),
                ('topic', models.ForeignKey(verbose_name='topic', to='tracker.Topic', help_text='Topic where this subtopic belongs')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='tag',
            name='topic',
        ),
        migrations.RemoveField(
            model_name='ticket',
            name='tag',
        ),
        migrations.DeleteModel(
            name='Tag',
        ),
        migrations.AddField(
            model_name='ticket',
            name='subtopic',
            field=models.ForeignKey(blank=True, to='tracker.Subtopic', help_text='Subtopic this ticket belongs to', null=True, verbose_name='subtopics'),
        ),
    ]
