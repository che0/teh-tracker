# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        for ticket in orm.Ticket.objects.all():
            try:
                ticket.topic = orm.Topic.objects.get(name=ticket.topic_str)
            except orm.Topic.DoesNotExist:
                topic = orm.Topic(name=ticket.topic_str)
                topic.save()
                ticket.topic = topic
            ticket.save()


    def backwards(self, orm):
        for ticket in orm.Ticket.objects.all():
            if ticket.topic != None:
                ticket.topic_str = ticket.topic.name
                ticket.save()


    models = {
        'tracker.ticket': {
            'Meta': {'ordering': "['-updated']", 'object_name': 'Ticket'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'requested_by': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tracker.Topic']", 'null': 'True', 'blank': 'True'}),
            'topic_str': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {})
        },
        'tracker.topic': {
            'Meta': {'ordering': "['name']", 'object_name': 'Topic'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'open_for_tickets': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['tracker']
