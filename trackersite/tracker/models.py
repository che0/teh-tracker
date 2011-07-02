# -*- coding: utf-8 -*-
import datetime

from django.contrib.comments.signals import comment_was_posted
from django.dispatch import receiver
from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

class Ticket(models.Model):
    """ One unit of tracked / paid stuff. """
    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('updated'))
    event_date = models.DateField(_('event date'), blank=True, null=True, help_text=_('Date of the event this ticket is about'))
    requested_by = models.CharField(verbose_name=_('requested by'), max_length=30, help_text=_('Person who created/requested for this ticket'))
    summary = models.CharField(_('summary'), max_length=100, help_text=_('Headline summary for the ticket'))
    topic = models.ForeignKey('tracker.Topic', verbose_name=_('topic'), help_text=_('Project topic this ticket belongs to'))
    status = models.CharField(_('status'), max_length=20, help_text=_('Status of this ticket'))
    description = models.TextField(_('description'), help_text=_('Detailed description; HTML is allowed for now, line breaks are auto-parsed'))
    amount_paid = models.DecimalField(_('amount paid'), max_digits=8, decimal_places=2, blank=True, null=True, help_text=_('amount actually paid for this ticket (in CZK)'))
    closed = models.BooleanField(_('closed'), default=False, help_text=_('Has this ticket been dealt with?'))
    
    def save(self, *args, **kwargs):
        self.updated = datetime.datetime.now()
        super(Ticket, self).save(*args, **kwargs)
    
    def _note_comment(self, **kwargs):
        self.save()
    
    def __unicode__(self):
        if self.closed:
            return _('%s [closed]') % self.summary
        else:
            return self.summary
        
    def get_absolute_url(self):
        return reverse('ticket_detail', kwargs={'pk':self.id})
    
    class Meta:
        verbose_name = _('Ticket')
        verbose_name_plural = _('Tickets')
        ordering = ['-updated']

class Topic(models.Model):
    """ Topics according to which the tickets are grouped. """
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

class MediaInfo(models.Model):
    """ Media related to particular tickets. """
    ticket = models.ForeignKey('tracker.Ticket', verbose_name=_('ticket'), help_text=_('Ticket this media info belongs to'))
    description = models.CharField(_('description'), max_length=100, help_text=_('media info item summary'))
    url = models.URLField(_('URL'), blank=True, verify_exists=False, help_text=_('URL of the related media files'))
    count = models.PositiveIntegerField(_('count'), blank=True, null=True, help_text=_('number of media files for this item'))
    
    def __unicode__(self):
        return self.description
    
    class Meta:
        verbose_name = _('Ticket media')
        verbose_name_plural = _('Ticket media')

class Expediture(models.Model):
    """ Expenses related to particular tickets. """
    ticket = models.ForeignKey('tracker.Ticket', verbose_name=_('ticket'), help_text=_('Ticket this expediture belongs to'))
    description = models.CharField(_('description'), max_length=100, help_text=_('media info item summary'))
    amount = models.DecimalField(_('amount'), max_digits=8, decimal_places=2, help_text=_('expediture amount in CZK'))
    
    def __unicode__(self):
        return _('%s (%s CZK)') % (self.description, self.amount)