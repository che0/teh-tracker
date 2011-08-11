# -*- coding: utf-8 -*-
import datetime

from django.contrib.comments.signals import comment_was_posted
from django.dispatch import receiver
from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _, string_concat
from django.conf import settings

class Ticket(models.Model):
    """ One unit of tracked / paid stuff. """
    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('updated'))
    event_date = models.DateField(_('event date'), blank=True, null=True, help_text=_('Date of the event this ticket is about'))
    requested_by = models.CharField(verbose_name=_('requested by'), max_length=30, help_text=_('Person who created/requested for this ticket'))
    summary = models.CharField(_('summary'), max_length=100, help_text=_('Headline summary for the ticket'))
    topic = models.ForeignKey('tracker.Topic', verbose_name=_('topic'), help_text=_('Project topic this ticket belongs to'))
    status = models.CharField(_('status'), max_length=100, help_text=_('Status of this ticket'))
    description = models.TextField(_('description'), blank=True, help_text=_("Space for further notes. If you're entering a trip tell us where did you go and what you did there."))
    amount_paid = models.DecimalField(_('amount paid'), max_digits=8, decimal_places=2, blank=True, null=True, help_text=string_concat(_('Amount actually paid for this ticket in'), ' ', settings.TRACKER_CURRENCY))
    closed = models.BooleanField(_('closed'), default=False, help_text=_('Has this ticket been dealt with?'))
    
    @staticmethod
    def currency():
        return settings.TRACKER_CURRENCY
    
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
    
    def media_count(self):
        return self.mediainfo_set.aggregate(objects=models.Count('id'), media=models.Sum('count'))
    
    def expeditures(self):
        return self.expediture_set.aggregate(count=models.Count('id'), amount=models.Sum('amount'))
    
    def can_edit(self, user):
        """ Can given user edit this ticket through a non-admin interface? """
        return (not self.closed) and (user.username == self.requested_by)
    
    class Meta:
        verbose_name = _('Ticket')
        verbose_name_plural = _('Tickets')
        ordering = ['-updated']

class Topic(models.Model):
    """ Topics according to which the tickets are grouped. """
    name = models.CharField(_('name'), max_length=80)
    open_for_tickets = models.BooleanField(_('open for tickets'), help_text=_('Is this topic open for ticket submissions from users?'))
    detailed_tickets = models.BooleanField(_('detailed tickets'), help_text=_('Does this topic use detailed ticket information (like media and expenses)?'))
    description = models.TextField(_('description'), blank=True, help_text=_('Detailed description; HTML is allowed for now, line breaks are auto-parsed'))
    form_description = models.TextField(_('form description'), blank=True, help_text=_('Description shown to users who enter tickets for this topic'))
    admin = models.ManyToManyField('auth.User', verbose_name=_('topic administrator'), help_text=_('Selected users will have administration access to this topic.'))
    
    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('topic_detail', kwargs={'pk':self.id})
    
    class Meta:
        verbose_name = _('Topic')
        verbose_name_plural = _('Topics')
        ordering = ['name']
        permissions = (
            ("supervisor", "Can edit all topics and tickets"),
        )

@receiver(comment_was_posted)
def ticket_note_comment(sender, comment, **kwargs):
    obj = comment.content_object 
    if type(obj) == Ticket:
        obj.save()

class MediaInfo(models.Model):
    """ Media related to particular tickets. """
    ticket = models.ForeignKey('tracker.Ticket', verbose_name=_('ticket'), help_text=_('Ticket this media info belongs to'))
    description = models.CharField(_('description'), max_length=255, help_text=_('Item description to show'))
    url = models.URLField(_('URL'), blank=True, verify_exists=False, help_text=_('Link to media files'))
    count = models.PositiveIntegerField(_('count'), blank=True, null=True, help_text=_('Number of files'))
    
    def __unicode__(self):
        return self.description
    
    class Meta:
        verbose_name = _('Ticket media')
        verbose_name_plural = _('Ticket media')

class Expediture(models.Model):
    """ Expenses related to particular tickets. """
    ticket = models.ForeignKey('tracker.Ticket', verbose_name=_('ticket'), help_text=_('Ticket this expediture belongs to'))
    description = models.CharField(_('description'), max_length=255, help_text=_('Description of this expediture'))
    amount = models.DecimalField(_('amount'), max_digits=8, decimal_places=2, help_text=string_concat(_('Expediture amount in'), ' ', settings.TRACKER_CURRENCY))
    
    def __unicode__(self):
        return _('%(description)s (%(amount)s %(currency)s)') % {'description':self.description, 'amount':self.amount, 'currency':settings.TRACKER_CURRENCY}
    
    class Meta:
        verbose_name = _('Ticket expediture')
        verbose_name_plural = _('Ticket expeditures')
