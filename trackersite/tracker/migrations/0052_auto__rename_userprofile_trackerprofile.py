# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        db.rename_table(u'tracker_userprofile', u'tracker_trackerprofile')


    def backwards(self, orm):
        db.rename_table(u'tracker_trackerprofile', u'tracker_userprofile')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'tracker.cluster': {
            'Meta': {'object_name': 'Cluster'},
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'more_tickets': ('django.db.models.fields.BooleanField', [], {}),
            'total_tickets': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'}),
            'total_transactions': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'})
        },
        u'tracker.document': {
            'Meta': {'object_name': 'Document'},
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payload': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'size': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'ticket': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tracker.Ticket']"})
        },
        u'tracker.expediture': {
            'Meta': {'object_name': 'Expediture'},
            'accounting_info': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ticket': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tracker.Ticket']"})
        },
        u'tracker.grant': {
            'Meta': {'ordering': "['full_name']", 'object_name': 'Grant'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        u'tracker.mediainfo': {
            'Meta': {'object_name': 'MediaInfo'},
            'count': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ticket': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tracker.Ticket']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        u'tracker.ticket': {
            'Meta': {'ordering': "['-sort_date']", 'object_name': 'Ticket'},
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tracker.Cluster']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'custom_state': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'event_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payment_status': ('django.db.models.fields.CharField', [], {'default': "'n/a'", 'max_length': '20'}),
            'rating_percentage': ('tracker.models.PercentageField', [], {'null': 'True', 'blank': 'True'}),
            'requested_text': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'requested_user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'sort_date': ('django.db.models.fields.DateField', [], {}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'supervisor_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tracker.Topic']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'tracker.ticketack': {
            'Meta': {'ordering': "['added']", 'object_name': 'TicketAck'},
            'ack_type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ticket': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tracker.Ticket']"})
        },
        u'tracker.topic': {
            'Meta': {'ordering': "['name']", 'object_name': 'Topic'},
            'admin': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'form_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'grant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tracker.Grant']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'open_for_tickets': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'ticket_expenses': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'ticket_media': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'tracker.trackerprofile': {
            'Meta': {'object_name': 'TrackerProfile'},
            'bank_account': ('django.db.models.fields.CharField', [], {'max_length': '120', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'other_contact': ('django.db.models.fields.CharField', [], {'max_length': '120', 'blank': 'True'}),
            'other_identification': ('django.db.models.fields.CharField', [], {'max_length': '120', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        },
        u'tracker.transaction': {
            'Meta': {'ordering': "['-date']", 'object_name': 'Transaction'},
            'accounting_info': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tracker.Cluster']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'other': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'other_text': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'tickets': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['tracker.Ticket']", 'symmetrical': 'False', 'blank': 'True'})
        }
    }

    complete_apps = ['tracker']