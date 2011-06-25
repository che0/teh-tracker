# -*- coding: utf-8 -*-
import datetime

from django.contrib.comments.signals import comment_was_posted
from django.dispatch import receiver
from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

class Ticket(models.Model):
    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('updated'))
    requested_by = models.CharField(verbose_name=_('requested by'), max_length=30, help_text=_('Person who created/requested for this ticket'))
    summary = models.CharField(_('summary'), max_length=100, help_text=_('Headline summary for the ticket'))
    topic = models.ForeignKey('tracker.Topic', verbose_name=_('topic'), help_text=_('Project topic this ticket belongs to'))
    status = models.CharField(_('status'), max_length=20, help_text=_('Status of this ticket'))
    description = models.TextField(_('description'), help_text=_('Detailed description; HTML is allowed for now, line breaks are auto-parsed'))
    
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
        verbose_name = _('Ticket')
        verbose_name_plural = _('Tickets')
        ordering = ['-updated']

class Topic(models.Model):
    name = models.CharField(_('name'), max_length=80)
    open_for_tickets = models.BooleanField(_('open for tickets'), help_text=_('Is this topic open for ticket submissions from users?'))
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Topic')
        verbose_name_plural = _('Topics')
        ordering = ['name']

@receiver(comment_was_posted)
def ticket_note_comment(sender, comment, **kwargs):
    obj = comment.content_object 
    if type(obj) == Ticket:
        obj.save()
