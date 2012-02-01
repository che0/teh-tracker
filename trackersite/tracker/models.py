# -*- coding: utf-8 -*-
import datetime

from django.contrib.comments.signals import comment_was_posted
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _, string_concat
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.conf import settings
from south.modelsinspector import add_introspection_rules

from tracker.clusters import ClusterUpdate

STATE_CHOICES = (
    ('draft', _('draft')),
    ('for consideration', _('for consideration')),
    ('accepted', _('accepted')),
    ('expenses filed', _('expenses filed')),
    ('closed', _('closed')),
    ('custom', _('custom')),
)

PAYMENT_STATUS_CHOICES = (
    ('n/a', _('n/a')),
    ('unpaid', _('unpaid')),
    ('partially paid', _('partially paid')),
    ('paid', _('paid')),
    ('overpaid', _('overpaid')),
)

class PercentageField(models.SmallIntegerField):
    """ Field that holds a percentage. """
    def formfield(self, **kwargs):
        defaults = {'min_value': 0, 'max_value':100}
        defaults.update(kwargs)
        return super(PercentageField, self).formfield(**defaults)
add_introspection_rules([], ["^tracker\.models\.PercentageField"])


class Ticket(models.Model):
    """ One unit of tracked / paid stuff. """
    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('updated'))
    sort_date = models.DateField(_('sort date'))
    event_date = models.DateField(_('event date'), blank=True, null=True, help_text=_('Date of the event this ticket is about'))
    requested_user = models.ForeignKey('auth.User', verbose_name=_('requested by'), blank=True, null=True, help_text=_('User who created/requested for this ticket'))
    requested_text = models.CharField(verbose_name=_('requested by (text)'), blank=True, max_length=30, help_text=_('Text description of who requested for this ticket, in case user is not filled in'))
    summary = models.CharField(_('summary'), max_length=100, help_text=_('Headline summary for the ticket'))
    topic = models.ForeignKey('tracker.Topic', verbose_name=_('topic'), help_text=_('Project topic this ticket belongs to'))
    state = models.CharField(_('state'), max_length=20, choices=STATE_CHOICES, help_text=_('Ticket state'))
    custom_state = models.CharField(_('custom state'), blank=True, max_length=100, help_text=_('Custom state description'))
    rating_percentage = PercentageField(_('rating percentage'), blank=True, null=True, help_text=_('Rating percentage set by topic administrator'))
    description = models.TextField(_('description'), blank=True, help_text=_("Space for further notes. If you're entering a trip tell us where did you go and what you did there."))
    supervisor_notes = models.TextField(_('supervisor notes'), blank=True, help_text=_("This space is for notes of project supervisors and accounting staff."))
    cluster = models.ForeignKey('Cluster', blank=True, null=True, on_delete=models.SET_NULL)
    payment_status = models.CharField(_('payment status'), max_length=20, default='n/a', choices=PAYMENT_STATUS_CHOICES)
    
    @staticmethod
    def currency():
        return settings.TRACKER_CURRENCY
    
    def save(self, *args, **kwargs):
        cluster_update_only = kwargs.pop('cluster_update_only', False)
        if not cluster_update_only:
            self.updated = datetime.datetime.now()
        
        if self.event_date != None:
            self.sort_date = self.event_date
        elif self.created != None:
            self.sort_date = self.created.date()
        else:
            self.sort_date = datetime.date.today()
        
        super(Ticket, self).save(*args, **kwargs)
        
        if not cluster_update_only:
            ClusterUpdate.perform(ticket_ids=set([self.id]))
    
    def _note_comment(self, **kwargs):
        self.save()
    
    def state_str(self):
        basic = _('unknown')
        if (self.state == 'custom') and self.custom_state:
            basic = self.custom_state
        else:
            for choice in STATE_CHOICES:
                if choice[0] == self.state:
                    basic = choice[1]
                    break
        
        if self.rating_percentage:
            return '%s [%s %%]' % (unicode(basic), self.rating_percentage)
        else:
            return basic
    state_str.admin_order_field = 'state'
    state_str.short_description = _('state')
            
    def __unicode__(self):
        return '%s: %s' % (self.id , self.summary)
    
    def requested_by(self):
        if self.requested_user != None:
            return self.requested_user.username
        else:
            return self.requested_text
    requested_by.short_description = _('requested by')
    
    def requested_by_html(self):
        if self.requested_user != None:
            out = '<a href="%s">%s</a>' % (self.requested_user.get_absolute_url(), escape(unicode(self.requested_user)))
            return mark_safe(out)
        else:
            return escape(self.requested_text)
    
    def get_absolute_url(self):
        return reverse('ticket_detail', kwargs={'pk':self.id})
    
    def media_count(self):
        return self.mediainfo_set.aggregate(objects=models.Count('id'), media=models.Sum('count'))
    
    def expeditures(self):
        return self.expediture_set.aggregate(count=models.Count('id'), amount=models.Sum('amount'))
    
    def accepted_expeditures(self):
        if (self.state != 'expenses filed') or (self.rating_percentage == None):
            return 0
        else:
            total = sum([x.amount for x in self.expediture_set.all()])
            return total * self.rating_percentage / 100
    
    def can_edit(self, user):
        """ Can given user edit this ticket through a non-admin interface? """
        return (self.state != 'expenses filed') and (self.state != 'closed') and (user == self.requested_user)
    
    def get_payment_status_class(self):
        classes = {'n/a':'na', 'unpaid':'unpaid', 'partially paid':'partially_paid', 'paid':'paid', 'overpaid':'overpaid'}
        return classes.get(self.payment_status, 'unknown')
    
    def associated_transactions_total(self):
        return self.transaction_set.all().aggregate(amount=models.Sum('amount'))['amount']
    
    class Meta:
        verbose_name = _('Ticket')
        verbose_name_plural = _('Tickets')
        ordering = ['-sort_date']

class Topic(models.Model):
    """ Topics according to which the tickets are grouped. """
    name = models.CharField(_('name'), max_length=80)
    open_for_tickets = models.BooleanField(_('open for tickets'), help_text=_('Is this topic open for ticket submissions from users?'))
    ticket_media = models.BooleanField(_('ticket media'), help_text=_('Does this topic track ticket media items?'))
    ticket_expenses = models.BooleanField(_('ticket expenses'), help_text=_('Does this topic track ticket expenses?'))
    description = models.TextField(_('description'), blank=True, help_text=_('Detailed description; HTML is allowed for now, line breaks are auto-parsed'))
    form_description = models.TextField(_('form description'), blank=True, help_text=_('Description shown to users who enter tickets for this topic'))
    admin = models.ManyToManyField('auth.User', verbose_name=_('topic administrator'), blank=True, help_text=_('Selected users will have administration access to this topic.'))
    
    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('topic_detail', kwargs={'pk':self.id})
    
    def media_count(self):
        return MediaInfo.objects.extra(where=['ticket_id in (select id from tracker_ticket where topic_id = %s)'], params=[self.id]).aggregate(objects=models.Count('id'), media=models.Sum('count'))
    
    def expeditures(self):
        return Expediture.objects.extra(where=['ticket_id in (select id from tracker_ticket where topic_id = %s)'], params=[self.id]).aggregate(count=models.Count('id'), amount=models.Sum('amount'))
    
    def accepted_expeditures(self):
        return sum([t.accepted_expeditures() for t in self.ticket_set.filter(state='expenses filed', rating_percentage__gt=0)])
    
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
    accounting_info = models.CharField(_('accounting info'), max_length=255, blank=True, help_text=_('Accounting info, this is editable only through admin field'))
    
    def __unicode__(self):
        return _('%(description)s (%(amount)s %(currency)s)') % {'description':self.description, 'amount':self.amount, 'currency':settings.TRACKER_CURRENCY}
    
    def save(self, *args, **kwargs):
        cluster_update_only = kwargs.pop('cluster_update_only', False)
        super(Expediture, self).save(*args, **kwargs)
        if not cluster_update_only:
            ClusterUpdate.perform(ticket_ids=set([self.ticket.id]))
    
    class Meta:
        verbose_name = _('Ticket expediture')
        verbose_name_plural = _('Ticket expeditures')

from django.contrib.auth.models import User

class TrackerUser(User):
    class Meta:
        proxy = True
    
    def get_absolute_url(self):
        return reverse('user_detail', kwargs={'username':self.username})
    
    def media_count(self):
        return MediaInfo.objects.extra(where=['ticket_id in (select id from tracker_ticket where requested_user_id = %s)'], params=[self.id]).aggregate(objects=models.Count('id'), media=models.Sum('count'))
    
    def expeditures(self):
        return Expediture.objects.extra(where=['ticket_id in (select id from tracker_ticket where requested_user_id = %s)'], params=[self.id]).aggregate(count=models.Count('id'), amount=models.Sum('amount'))

    def accepted_expeditures(self):
        return sum([t.accepted_expeditures() for t in self.ticket_set.filter(state='expenses filed', rating_percentage__gt=0)])
    
    def transactions(self):
        return Transaction.objects.filter(other=self).aggregate(count=models.Count('id'), amount=models.Sum('amount'))
    
    def balance(self):
        """ User's financial balance towards us. Positive amount means we owe him money. """
        transaction_total = self.transactions()['amount']
        if transaction_total == None:
            transaction_total = 0
        return self.accepted_expeditures() - transaction_total

class Transaction(models.Model):
    """ One payment to or from the user. """
    date = models.DateField(_('date'))
    other = models.ForeignKey('auth.User', verbose_name=_('other party'), help_text=_('The other party; user who sent or received the payment'))
    amount = models.DecimalField(_('amount'), max_digits=8, decimal_places=2, help_text=_('Payment amount; Positive value means transaction to the user, negative is a transaction from the user'))
    description = models.CharField(_('description'), max_length=255, help_text=_('Description of this transaction'))
    accounting_info = models.CharField(_('accounting info'), max_length=255, blank=True, help_text=_('Accounting info'))
    tickets = models.ManyToManyField(Ticket, verbose_name=_('related tickets'), blank=True, help_text=_('Tickets this trackaction is related to'))
    cluster = models.ForeignKey('Cluster', blank=True, null=True, on_delete=models.SET_NULL)
    
    def __unicode__(self):
        out = u'%s, %s %s' % (self.date, self.amount, settings.TRACKER_CURRENCY)
        if self.description != None:
           out += ': ' + self.description 
        return out
    
    def ticket_ids(self):
        return u', '.join([unicode(t.id) for t in self.tickets.order_by('id')])
    
    def tickets_by_id(self):
        return self.tickets.order_by('id')
    
    def save(self, *args, **kwargs):
        cluster_update_only = kwargs.pop('cluster_update_only', False)
        super(Transaction, self).save(*args, **kwargs)
        if not cluster_update_only:
            ClusterUpdate.perform(transaction_ids=set([self.id]))
    
    @staticmethod
    def currency():
        return settings.TRACKER_CURRENCY
    
    class Meta:
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        ordering = ['-date']

class Cluster(models.Model):
    """ This is an auxiliary/cache model used to track relationships between tickets and payments. """
    id = models.IntegerField(primary_key=True) # cluster ID is always the id of its lowest-numbered ticket
    more_tickets = models.BooleanField() # does this cluster have more tickets?
    total_tickets = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True) # refreshed on cluster status update
    total_transactions = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True) # refreshed on cluster status update
    
    def get_absolute_url(self):
        return reverse('cluster_detail', kwargs={'pk':self.id})
    
    def get_status(self):
        paid = self.total_transactions or 0
        tickets = self.total_tickets or 0
        if paid < tickets:
            if paid == 0:
                return 'unpaid'
            else:
                return 'partially paid'
        elif paid == tickets:
            if tickets == 0:
                return 'n/a'
            else:
                return 'paid'
        else: # paid > tickets
            return 'overpaid'
    
    def update_status(self):
        """ Recounts all the summaries and updates payment status in tickets. """
        self.total_tickets = sum([t.accepted_expeditures() for t in self.ticket_set.all()])
        self.total_transactions = self.transaction_set.all().aggregate(amount=models.Sum('amount'))['amount']
        status = self.get_status()
        for t in self.ticket_set.all():
            t.payment_status = status
            t.save(cluster_update_only=True)
        self.save()

@receiver(models.signals.m2m_changed)
def cluster_note_transaction_link(sender, instance, action, **kwargs):
    if type(instance) == Transaction and action in ('post_add', 'post_remove', 'post_clear'):
        ClusterUpdate.perform(transaction_ids=set([instance.id]))
