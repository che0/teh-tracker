# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Ticket.requested_by'
        db.add_column('tracker_ticket', 'requested_by', self.gf('django.db.models.fields.CharField')(default='unknown', max_length=30), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Ticket.requested_by'
        db.delete_column('tracker_ticket', 'requested_by')


    models = {
        'tracker.ticket': {
            'Meta': {'ordering': "['-updated']", 'object_name': 'Ticket'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'requested_by': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'topic': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {})
        }
    }

    complete_apps = ['tracker']
