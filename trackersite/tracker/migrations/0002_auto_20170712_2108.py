# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tracker.models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0002_myisam_to_innodb'),
    ]

    operations = [
        migrations.CreateModel(
            name='Preexpediture',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(help_text='Description of this preexpediture', max_length=255, verbose_name='description')),
                ('amount', models.DecimalField(help_text='Preexpediture amount in CZK', verbose_name='amount', max_digits=8, decimal_places=2)),
                ('wage', models.BooleanField(default=False, verbose_name='wage')),
            ],
            options={
                'verbose_name': 'Ticket preexpediture',
                'verbose_name_plural': 'Ticket preexpeditures',
            },
        ),
        migrations.AddField(
            model_name='expediture',
            name='paid',
            field=models.BooleanField(default=False, verbose_name='paid'),
        ),
        migrations.AddField(
            model_name='expediture',
            name='wage',
            field=models.BooleanField(default=False, verbose_name='wage'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='deposit',
            field=tracker.models.DecimalRangeField(default=0, help_text="If you are requesting a financial deposit, please fill here its amount. Maximum amount is sum of preexpeditures. If you aren't requesting a deposit, fill here 0.", verbose_name='deposit', max_digits=8, decimal_places=2),
        ),
        migrations.AddField(
            model_name='ticket',
            name='mandatory_report',
            field=models.BooleanField(default=False, help_text='Is report mandatory?', verbose_name='report mandatory'),
        ),
        migrations.AddField(
            model_name='topic',
            name='ticket_preexpenses',
            field=models.BooleanField(default=True, help_text='Does this topic track preexpenses?', verbose_name='ticket preexpenses'),
        ),
        migrations.AlterField(
            model_name='ticketack',
            name='ack_type',
            field=models.CharField(max_length=20, choices=[(b'user_precontent', 'presubmitted'), (b'precontent', 'preaccepted'), (b'user_content', 'submitted'), (b'content', 'accepted'), (b'user_docs', 'expense documents submitted'), (b'docs', 'expense documents filed'), (b'archive', 'archived'), (b'close', 'closed')]),
        ),
        migrations.AddField(
            model_name='preexpediture',
            name='ticket',
            field=models.ForeignKey(verbose_name='ticket', to='tracker.Ticket', help_text='Ticket this preexpediture belogns to'),
        ),
    ]
