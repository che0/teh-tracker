# -*- coding: utf-8 -*-
import datetime

from django.contrib.comments.signals import comment_was_posted
from django.dispatch import receiver
from django.db import models
from django.core.urlresolvers import reverse

class Ticket(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField()
    requested_by = models.CharField(max_length=30, help_text=u'Person who created/requested for this ticket')
    summary = models.CharField(max_length=100, help_text=u'Headline summary for the ticket')
    topic = models.CharField(max_length=80, help_text=u'Topic this ticket belongs to')
    status = models.CharField(max_length=20, help_text=u'Status of this ticket')
    description = models.TextField(help_text=u'Detailed description; HTML is allowed for now, line breaks are auto-parsed')
    
    def save(self, *args, **kwargs):
        self.updated = datetime.datetime.now()
        super(Ticket, self).save(*args, **kwargs)
    
    def _note_comment(self, **kwargs):
        self.save()
    
    def __unicode__(self):
        return self.summary
        
    def get_absolute_url(self):
        return reverse('ticket_detail', kwargs={'pk':self.id})
    
    class Meta:
        ordering = ['-updated']

@receiver(comment_was_posted)
def ticket_note_comment(sender, comment, **kwargs):
    obj = comment.content_object 
    if type(obj) == Ticket:
        obj.save()
