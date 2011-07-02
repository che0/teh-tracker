# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Expediture'
        db.create_table('tracker_expediture', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ticket', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tracker.Ticket'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('amount', self.gf('django.db.models.fields.DecimalField')(max_digits=8, decimal_places=2)),
        ))
        db.send_create_signal('tracker', ['Expediture'])

        # Adding model 'MediaInfo'
        db.create_table('tracker_mediainfo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ticket', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tracker.Ticket'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('count', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('tracker', ['MediaInfo'])

        # Adding field 'Ticket.event_date'
        db.add_column('tracker_ticket', 'event_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True), keep_default=False)

        # Adding field 'Ticket.amount_paid'
        db.add_column('tracker_ticket', 'amount_paid', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=8, decimal_places=2, blank=True), keep_default=False)

        # Adding field 'Ticket.closed'
        db.add_column('tracker_ticket', 'closed', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)


    def backwards(self, orm):
        
        # Deleting model 'Expediture'
        db.delete_table('tracker_expediture')

        # Deleting model 'MediaInfo'
        db.delete_table('tracker_mediainfo')

        # Deleting field 'Ticket.event_date'
        db.delete_column('tracker_ticket', 'event_date')

        # Deleting field 'Ticket.amount_paid'
        db.delete_column('tracker_ticket', 'amount_paid')

        # Deleting field 'Ticket.closed'
        db.delete_column('tracker_ticket', 'closed')


    models = {
        'tracker.expediture': {
            'Meta': {'object_name': 'Expediture'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ticket': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tracker.Ticket']"})
        },
        'tracker.mediainfo': {
            'Meta': {'object_name': 'MediaInfo'},
            'count': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ticket': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tracker.Ticket']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'tracker.ticket': {
            'Meta': {'ordering': "['-updated']", 'object_name': 'Ticket'},
            'amount_paid': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'}),
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'event_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
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
