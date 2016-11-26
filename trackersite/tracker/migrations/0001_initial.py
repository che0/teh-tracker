# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tracker.models
from django.conf import settings
import django.db.models.deletion
import django.core.files.storage
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Cluster',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('more_tickets', models.BooleanField()),
                ('total_tickets', models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)),
                ('total_transactions', models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filename', models.CharField(help_text=b'Document filename', max_length=120, validators=[django.core.validators.RegexValidator(b'^[-_\\.A-Za-z0-9]+\\.[A-Za-z0-9]+$', message='We need a sane file name, such as my-invoice123.jpg')])),
                ('size', models.PositiveIntegerField()),
                ('content_type', models.CharField(max_length=64)),
                ('description', models.CharField(help_text=b'Optional further description of the document', max_length=255, blank=True)),
                ('payload', models.FileField(storage=django.core.files.storage.FileSystemStorage(location=settings.TRACKER_DOCS_ROOT), upload_to=b'tickets/%Y/')),
            ],
            options={
                'permissions': (('see_all_docs', 'Can see all documents'), ('edit_all_docs', 'Can edit all documents')),
            },
        ),
        migrations.CreateModel(
            name='Expediture',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(help_text='Description of this expediture', max_length=255, verbose_name='description')),
                ('amount', models.DecimalField(help_text='Expediture amount in CZK', verbose_name='amount', max_digits=8, decimal_places=2)),
                ('accounting_info', models.CharField(help_text='Accounting info, this is editable only through admin field', max_length=255, verbose_name='accounting info', blank=True)),
            ],
            options={
                'verbose_name': 'Ticket expediture',
                'verbose_name_plural': 'Ticket expeditures',
            },
        ),
        migrations.CreateModel(
            name='Grant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('full_name', models.CharField(help_text='Full name for headlines and such', max_length=80, verbose_name='full name')),
                ('short_name', models.CharField(help_text='Shorter name for use in tables', max_length=16, verbose_name='short name')),
                ('slug', models.SlugField(help_text='Shortcut for usage in URLs', verbose_name='slug')),
                ('description', models.TextField(help_text='Detailed description; HTML is allowed for now, line breaks are auto-parsed', verbose_name='description', blank=True)),
            ],
            options={
                'ordering': ['full_name'],
                'verbose_name': 'Grant',
                'verbose_name_plural': 'Grants',
            },
        ),
        migrations.CreateModel(
            name='MediaInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(help_text='Item description to show', max_length=255, verbose_name='description')),
                ('url', models.URLField(help_text='Link to media files', verbose_name='URL', blank=True)),
                ('count', models.PositiveIntegerField(help_text='Number of files', null=True, verbose_name='count', blank=True)),
            ],
            options={
                'verbose_name': 'Ticket media',
                'verbose_name_plural': 'Ticket media',
            },
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('updated', models.DateTimeField(verbose_name='updated')),
                ('sort_date', models.DateField(verbose_name='sort date')),
                ('event_date', models.DateField(help_text='Date of the event this ticket is about', null=True, verbose_name='event date', blank=True)),
                ('requested_text', models.CharField(help_text='Text description of who requested for this ticket, in case user is not filled in', max_length=30, verbose_name='requested by (text)', blank=True)),
                ('summary', models.CharField(help_text='Headline summary for the ticket', max_length=100, verbose_name='summary')),
                ('custom_state', models.CharField(help_text='Custom state description', max_length=100, verbose_name='custom state', blank=True)),
                ('rating_percentage', tracker.models.PercentageField(help_text='Rating percentage set by topic administrator', null=True, verbose_name='rating percentage', blank=True)),
                ('description', models.TextField(help_text="Space for further notes. If you're entering a trip tell us where did you go and what you did there.", verbose_name='description', blank=True)),
                ('supervisor_notes', models.TextField(help_text='This space is for notes of project supervisors and accounting staff.', verbose_name='supervisor notes', blank=True)),
                ('payment_status', models.CharField(default=b'n/a', max_length=20, verbose_name='payment status', choices=[(b'n_a', 'n/a'), (b'unpaid', 'unpaid'), (b'partially_paid', 'partially paid'), (b'paid', 'paid'), (b'overpaid', 'overpaid')])),
                ('cluster', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='tracker.Cluster', null=True)),
                ('requested_user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, help_text='User who created/requested for this ticket', null=True, verbose_name='requested by')),
            ],
            options={
                'ordering': ['-sort_date'],
                'verbose_name': 'Ticket',
                'verbose_name_plural': 'Tickets',
            },
        ),
        migrations.CreateModel(
            name='TicketAck',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ack_type', models.CharField(max_length=20, choices=[(b'user_content', 'submitted'), (b'content', 'accepted'), (b'user_docs', 'expense documents submitted'), (b'docs', 'expense documents filed'), (b'archive', 'archived'), (b'close', 'closed')])),
                ('added', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('comment', models.CharField(max_length=255, blank=True)),
                ('added_by', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('ticket', models.ForeignKey(to='tracker.Ticket')),
            ],
            options={
                'ordering': ['added'],
            },
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80, verbose_name='name')),
                ('open_for_tickets', models.BooleanField(default=True, help_text='Is this topic open for ticket submissions from users?', verbose_name='open for tickets')),
                ('ticket_media', models.BooleanField(default=True, help_text='Does this topic track ticket media items?', verbose_name='ticket media')),
                ('ticket_expenses', models.BooleanField(default=True, help_text='Does this topic track ticket expenses?', verbose_name='ticket expenses')),
                ('description', models.TextField(help_text='Detailed description; HTML is allowed for now, line breaks are auto-parsed', verbose_name='description', blank=True)),
                ('form_description', models.TextField(help_text='Description shown to users who enter tickets for this topic', verbose_name='form description', blank=True)),
                ('admin', models.ManyToManyField(help_text='Selected users will have administration access to this topic.', to=settings.AUTH_USER_MODEL, verbose_name='topic administrator', blank=True)),
                ('grant', models.ForeignKey(verbose_name='grant', to='tracker.Grant', help_text='Grant project where this topic belongs')),
            ],
            options={
                'ordering': ['-open_for_tickets', 'name'],
                'verbose_name': 'Topic',
                'verbose_name_plural': 'Topics',
                'permissions': (('supervisor', 'Can edit all topics and tickets'),),
            },
        ),
        migrations.CreateModel(
            name='TrackerProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bank_account', models.CharField(help_text='Bank account information for money transfers', max_length=120, verbose_name='Bank account', blank=True)),
                ('other_contact', models.CharField(help_text='Other contact such as wiki account; can be useful in case of topic administrators need to clarify some information', max_length=120, verbose_name='Other contact', blank=True)),
                ('other_identification', models.CharField(help_text='Address, or other identification information, so we know who are we sending money to', max_length=120, verbose_name='Other identification', blank=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(verbose_name='date')),
                ('other_text', models.CharField(help_text='The other party; this text is used when user is not selected', max_length=60, verbose_name='other party (text)', blank=True)),
                ('amount', models.DecimalField(help_text='Payment amount; Positive value means transaction to the user, negative is a transaction from the user', verbose_name='amount', max_digits=8, decimal_places=2)),
                ('description', models.CharField(help_text='Description of this transaction', max_length=255, verbose_name='description')),
                ('accounting_info', models.CharField(help_text='Accounting info', max_length=255, verbose_name='accounting info', blank=True)),
                ('cluster', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='tracker.Cluster', null=True)),
                ('other', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, help_text='The other party; user who sent or received the payment', null=True, verbose_name='other party')),
                ('tickets', models.ManyToManyField(help_text='Tickets this trackaction is related to', to='tracker.Ticket', verbose_name='related tickets', blank=True)),
            ],
            options={
                'ordering': ['-date'],
                'verbose_name': 'Transaction',
                'verbose_name_plural': 'Transactions',
            },
        ),
        migrations.AddField(
            model_name='ticket',
            name='topic',
            field=models.ForeignKey(verbose_name='topic', to='tracker.Topic', help_text='Project topic this ticket belongs to'),
        ),
        migrations.AddField(
            model_name='mediainfo',
            name='ticket',
            field=models.ForeignKey(verbose_name='ticket', to='tracker.Ticket', help_text='Ticket this media info belongs to'),
        ),
        migrations.AddField(
            model_name='expediture',
            name='ticket',
            field=models.ForeignKey(verbose_name='ticket', to='tracker.Ticket', help_text='Ticket this expediture belongs to'),
        ),
        migrations.AddField(
            model_name='document',
            name='ticket',
            field=models.ForeignKey(to='tracker.Ticket'),
        ),
    ]
