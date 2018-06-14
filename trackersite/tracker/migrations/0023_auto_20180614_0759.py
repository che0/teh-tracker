# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0022_auto_20180606_2202'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80, verbose_name='name')),
                ('description', models.TextField(help_text='Description shown to users who enter tickets for this tag', verbose_name='description', blank=True)),
                ('topic', models.ForeignKey(verbose_name='topic', to='tracker.Topic', help_text='Topic where this tag belongs')),
            ],
        ),
        migrations.AddField(
            model_name='ticket',
            name='tags',
            field=models.ManyToManyField(help_text='Tags this ticket belongs to', to='tracker.Tag', verbose_name='tags'),
        ),
    ]
