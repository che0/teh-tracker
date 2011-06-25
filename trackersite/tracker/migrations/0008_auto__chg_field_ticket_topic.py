# -*- coding: utf-8 -*-
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    default_topic_id = None
    
    def get_default_topic_id(self, orm):
        if self.default_topic_id != None:
            return self.default_topic_id
        
        try:
            self.default_topic_id = orm.Topic.objects.get(name='blank').id
        except orm.Topic.DoesNotExist:
            topic = orm.Topic(name='blank')
            topic.save()
            self.default_topic_id = topic.id
        return self.default_topic_id

    def forwards(self, orm):
        if not db.dry_run:
            for ticket in orm.Ticket.objects.all():
                if ticket.topic_id == None:
                    ticket.topic_id = self.get_default_topic_id(orm)
                    ticket.save()
        
        # Changing field 'Ticket.topic'
        db.alter_column('tracker_ticket', 'topic_id', self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['tracker.Topic']))


    def backwards(self, orm):
        
        # Changing field 'Ticket.topic'
        db.alter_column('tracker_ticket', 'topic_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tracker.Topic'], null=True))


    models = {
        'tracker.ticket': {
            'Meta': {'ordering': "['-updated']", 'object_name': 'Ticket'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'requested_by': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tracker.Topic']"}),
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
