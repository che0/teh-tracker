# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        for t in orm.Ticket.objects.all():
            if t.payment_status in (None, ''):
                t.payment_status = 'n/a'
                t.save()


    def backwards(self, orm):
        for t in orm.Ticket.objects.all():
            if t.payment_status == 'n/a':
                t.payment_status = None
                t.save()


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'tracker.cluster': {
            'Meta': {'object_name': 'Cluster'},
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'more_tickets': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'total_tickets': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'}),
            'total_transactions': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'})
        },
        'tracker.expediture': {
            'Meta': {'object_name': 'Expediture'},
            'accounting_info': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ticket': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tracker.Ticket']"})
        },
        'tracker.mediainfo': {
            'Meta': {'object_name': 'MediaInfo'},
            'count': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ticket': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tracker.Ticket']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'tracker.ticket': {
            'Meta': {'ordering': "['-sort_date']", 'object_name': 'Ticket'},
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tracker.Cluster']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'custom_state': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'event_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payment_status': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'rating_percentage': ('tracker.models.PercentageField', [], {'null': 'True', 'blank': 'True'}),
            'requested_text': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'requested_user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'sort_date': ('django.db.models.fields.DateField', [], {}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'supervisor_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tracker.Topic']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {})
        },
        'tracker.topic': {
            'Meta': {'ordering': "['name']", 'object_name': 'Topic'},
            'admin': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'form_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'open_for_tickets': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'ticket_expenses': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'ticket_media': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'tracker.transaction': {
            'Meta': {'ordering': "['-date']", 'object_name': 'Transaction'},
            'accounting_info': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tracker.Cluster']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'other': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'tickets': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['tracker.Ticket']", 'symmetrical': 'False', 'blank': 'True'})
        }
    }

    complete_apps = ['tracker']
