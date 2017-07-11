# -*- coding: utf-8 -*-
import datetime
import decimal

from django_comments.signals import comment_was_posted
from django.db.models.signals import post_save, post_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _, string_concat
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.validators import RegexValidator
from django.core.urlresolvers import NoReverseMatch
from django.core.cache import cache
from django import template

from users.models import UserWrapper
from tracker.clusters import ClusterUpdate

PAYMENT_STATUS_CHOICES = (
    ('n_a', _('n/a')),
    ('unpaid', _('unpaid')),
    ('partially_paid', _('partially paid')),
    ('paid', _('paid')),
    ('overpaid', _('overpaid')),
)

ACK_TYPES = (
    ('user_precontent', _('presubmitted')),
    ('precontent', _('preaccepted')),
    ('user_content', _('submitted')),
    ('content', _('accepted')),
    ('user_docs', _('expense documents submitted')),
    ('docs', _('expense documents filed')),
    ('archive', _('archived')),
    ('close', _('closed')),
)

USER_EDITABLE_ACK_TYPES = ('user_precontent', 'user_docs', 'user_content')

def uber_ack(ack_type):
    """ Return 'super-ack' for given user-editable ack. """
    return {
        'user_precontent': 'precontent',
        'user_content': 'content',
        'user_docs':'docs',
    }[ack_type]

class PercentageField(models.SmallIntegerField):
    """ Field that holds a percentage. """
    def formfield(self, **kwargs):
        defaults = {'min_value': 0, 'max_value':100}
        defaults.update(kwargs)
        return super(PercentageField, self).formfield(**defaults)

class CachedModel(models.Model):
    """ Model which has some values cached """
    
    def _get_item_key(self, name):
        return u'm:%s:%s:%s' % (self.__class__.__name__, self.id, name)
    
    def _get_version_key(self):
        return u'm:%s:%s:_version' % (self.__class__.__name__, self.id)
    
    def _cache_version(self):
        return cache.get(self._get_version_key()) or 1
    
    def flush_cache(self):
        cache.set(self._get_version_key(), self._cache_version() + 1)
    flush_cache.alters_data = True
    
    @staticmethod
    def cached_getter(raw_method):
        def wrapped(self):
            key = self._get_item_key(raw_method.__name__)
            version = self._cache_version()
            cached = cache.get(key, version=version)
            if cached is not None:
                return cached
            else:
                value = raw_method(self)
                cache.set(key, value, version=version)
                return value
        
        return wrapped 
    
    class Meta:
        abstract = True
cached_getter = CachedModel.cached_getter

class Ticket(CachedModel):
    """ One unit of tracked / paid stuff. """
    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('updated'))
    sort_date = models.DateField(_('sort date'))
    event_date = models.DateField(_('event date'), blank=True, null=True, help_text=_('Date of the event this ticket is about'))
    requested_user = models.ForeignKey('auth.User', verbose_name=_('requested by'), blank=True, null=True, help_text=_('User who created/requested for this ticket'))
    requested_text = models.CharField(verbose_name=_('requested by (text)'), blank=True, max_length=30, help_text=_('Text description of who requested for this ticket, in case user is not filled in'))
    summary = models.CharField(_('summary'), max_length=100, help_text=_('Headline summary for the ticket'))
    topic = models.ForeignKey('tracker.Topic', verbose_name=_('topic'), help_text=_('Project topic this ticket belongs to'))
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
        
        self.flush_cache()
    
    def _note_comment(self, **kwargs):
        self.save()
    
    def state_str(self):
        if self.custom_state:
            return self.custom_state
        
        acks = self.ack_set()
        if 'closed' in acks:
            return _('closed')
        elif 'archive' in acks:
            return _('archived')
        elif 'content' in acks:
            if not self.rating_percentage:
                return _('waiting for content rating')
            
            if 'docs' in acks:
                return _('complete')
            elif 'user_docs' in acks:
                return _('waiting for filing of documents')
            else:
                return _('waiting for document submission')
        elif 'precontent' in acks:
            if 'user_content' in acks:
                return _('waiting for approval')
            else:
                return _('waiting for event')
        elif 'user_content' in acks and 'user_precontent' not in acks:
            return _('waiting for approval')
        else:
            if 'user_precontent' in acks:
                return _('waiting for preapproval')
            else:
                return _('draft')
    state_str.admin_order_field = 'state'
    state_str.short_description = _('state')
            
    def __unicode__(self):
        return '%s: %s' % (self.id , self.summary)
    
    @cached_getter
    def requested_by(self):
        if self.requested_user != None:
            return self.requested_user.username
        else:
            return self.requested_text
    requested_by.short_description = _('requested by')
    
    def requested_by_html(self):
        if self.requested_user != None:
            return UserWrapper(self.requested_user).get_html_link()
        else:
            return escape(self.requested_text)
    
    @cached_getter
    def requested_user_details(self):
        if self.requested_user != None:
            out = u'%s: %s<br />%s: %s' % (
                _('E-mail'), escape(self.requested_user.email),
                _('Other contact'), escape(self.requested_user.trackerprofile.other_contact),
            )
            return mark_safe(out)
        else:
            return _('no tracker account listed')
    requested_user_details.short_description = _('Requester details')
    
    def get_absolute_url(self):
        return reverse('ticket_detail', kwargs={'pk':self.id})
    
    @cached_getter
    def media_count(self):
        return self.mediainfo_set.aggregate(objects=models.Count('id'), media=models.Sum('count'))
    
    @cached_getter
    def expeditures(self):
        return self.expediture_set.aggregate(count=models.Count('id'), amount=models.Sum('amount'))

    @cached_getter
    def preexpeditures(self):
        return self.preexpediture_set.aggregate(count=models.Count('id'), amount=models.Sum('amount'))
    
    @cached_getter
    def accepted_expeditures(self):
        if not self.has_all_acks('content', 'docs', 'archive') or (self.rating_percentage == None):
            return decimal.Decimal(0)
        else:
            total = sum([x.amount for x in self.expediture_set.all()], decimal.Decimal(0))
            reduced = total * self.rating_percentage / 100
            return reduced.quantize(decimal.Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
    
    def can_edit(self, user):
        """ Can given user edit this ticket through a non-admin interface? """
        acks = self.ack_set()
        return ('archive' not in acks) and ('close' not in acks) and (user == self.requested_user)
    
    def can_see_documents(self, user):
        """ Can given user see documents belonging to this ticket? """
        return (user == self.requested_user) or user.has_perm('tracker.see_all_docs') or user.has_perm('tracker.edit_all_docs')
    
    def can_edit_documents(self, user):
        """ Can given user edit documents belonging to this ticket? """
        return (user == self.requested_user) or user.has_perm('tracker.edit_all_docs')
    
    @cached_getter
    def associated_transactions_total(self):
        return self.transaction_set.all().aggregate(amount=models.Sum('amount'))['amount']
    
    @cached_getter
    def ack_set(self):
        return set([x.ack_type for x in self.ticketack_set.only('ack_type')])
    
    def has_ack(self, ack_type):
        return ack_type in self.ack_set()
    
    def has_all_acks(self, *wanted_acks):
        acks = self.ack_set()
        for wanted in wanted_acks:
            if wanted not in acks:
                return False
        return True
    
    def add_acks(self, *acks):
        """ Adds acks, mostly for testing. """
        for ack in acks:
            self.ticketack_set.create(ack_type=ack, comment='system operation')
        self.flush_cache()
    
    @cached_getter
    def possible_user_ack_types(self):
        """ List of possible ack types, that can be added by ticket requester. """
        out = []
        for ack_type in USER_EDITABLE_ACK_TYPES:
            if not self.has_ack(ack_type) and not self.has_ack(uber_ack(ack_type)):
                out.append(ack_type)
        return out
    
    @cached_getter
    def possible_user_acks(self):
        """ List of PossibleAck objects, that can be added by ticket requester. """
        return [PossibleAck(ack_type) for ack_type in self.possible_user_ack_types()]
    
    def flush_cache(self):
        super(Ticket, self).flush_cache()
        self.topic.flush_cache()
    
    class Meta:
        verbose_name = _('Ticket')
        verbose_name_plural = _('Tickets')
        ordering = ['-sort_date']

class FinanceStatus(object):
    """ This is not a model, but rather a representation of topic finance status. """
    
    def __init__(self, fuzzy=False, unpaid=0, paid=0, overpaid=0):
        self.fuzzy = fuzzy
        # we set fuzzy flag if there is partially paid/overpaid cluster that involves more tickets
        # and hence our sums may not make much sense
        
        self.unpaid = unpaid
        self.paid = paid
        self.overpaid = overpaid
        
        self.seen_cluster_ids = set()
    
    def __repr__(self):
        return 'FinanceStatus(fuzzy=%s, unpaid=%s, paid=%s, overpaid=%s)' % (self.fuzzy, self.unpaid, self.paid, self.overpaid)
    
    def _equals(self, other):
        return self.fuzzy == other.fuzzy and self.unpaid == other.unpaid and self.paid == other.paid and self.overpaid == other.overpaid
    
    def __eq__(self, other):
        try:
            return self._equals(other)
        except AttributeError:
            return NotImplemented
    
    def __ne__(self, other):
        try:
            return not self._equals(other)
        except AttributeError:
            return NotImplemented
    
    def add_ticket(self, ticket):
        if ticket.payment_status == 'unpaid':
            self.unpaid += ticket.accepted_expeditures()
        elif ticket.payment_status == 'paid':
            self.paid += ticket.accepted_expeditures()
        elif ticket.payment_status in ('partially_paid', 'overpaid'):
            cluster_topics = ticket.cluster.get_topic_count()
            if cluster_topics > 1:
                self.fuzzy = True
            if ticket.cluster.id not in self.seen_cluster_ids:
                self.seen_cluster_ids.add(ticket.cluster.id)
                if ticket.payment_status == 'partially_paid':
                    self.paid += ticket.cluster.total_transactions / cluster_topics
                    self.unpaid += (ticket.cluster.total_tickets - ticket.cluster.total_transactions) / cluster_topics
                else: # overpaid
                    self.paid += ticket.cluster.total_tickets / cluster_topics
                    self.overpaid += (ticket.cluster.total_transactions - ticket.cluster.total_tickets) / cluster_topics
    
    def add_finance(self, other):
        self.fuzzy = self.fuzzy or other.fuzzy
        self.unpaid += other.unpaid
        self.paid += other.paid
        self.overpaid += other.overpaid
        self.seen_cluster_ids = self.seen_cluster_ids.union(other.seen_cluster_ids)
    
    def as_dict(self):
        return {'fuzzy':self.fuzzy, 'unpaid':self.unpaid, 'paid':self.paid, 'overpaid':self.overpaid}


class Topic(CachedModel):
    """ Topics according to which the tickets are grouped. """
    name = models.CharField(_('name'), max_length=80)
    grant = models.ForeignKey('tracker.Grant', verbose_name=_('grant'), help_text=_('Grant project where this topic belongs'))
    open_for_tickets = models.BooleanField(_('open for tickets'), default=True, help_text=_('Is this topic open for ticket submissions from users?'))
    ticket_media = models.BooleanField(_('ticket media'), default=True, help_text=_('Does this topic track ticket media items?'))
    ticket_expenses = models.BooleanField(_('ticket expenses'), default=True, help_text=_('Does this topic track ticket expenses?'))
    ticket_preexpenses = models.BooleanField(_('ticket preexpenses'), default=True, help_text=_('Does this topic track preexpenses?'))
    description = models.TextField(_('description'), blank=True, help_text=_('Detailed description; HTML is allowed for now, line breaks are auto-parsed'))
    form_description = models.TextField(_('form description'), blank=True, help_text=_('Description shown to users who enter tickets for this topic'))
    admin = models.ManyToManyField('auth.User', verbose_name=_('topic administrator'), blank=True, help_text=_('Selected users will have administration access to this topic.'))
    
    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('topic_detail', kwargs={'pk':self.id})
    
    @cached_getter
    def media_count(self):
        return MediaInfo.objects.extra(where=['ticket_id in (select id from tracker_ticket where topic_id = %s)'], params=[self.id]).aggregate(objects=models.Count('id'), media=models.Sum('count'))
    
    @cached_getter
    def expeditures(self):
        return Expediture.objects.extra(where=['ticket_id in (select id from tracker_ticket where topic_id = %s)'], params=[self.id]).aggregate(count=models.Count('id'), amount=models.Sum('amount'))

    @cached_getter
    def preexpeditures(self):
        return Prexpediture.objects.extra(where=['ticket_id in (select id from tracker_ticket where topic_id = %s)'], params=[self.id]).aggregate(count=models.Count('id'), amount=models.Sum('amount'))
    
    @cached_getter
    def accepted_expeditures(self):
        return sum([t.accepted_expeditures() for t in self.ticket_set.filter(rating_percentage__gt=0)])
    
    @cached_getter
    def tickets_per_payment_status(self):
        out = {}
        for s in self.ticket_set.values('payment_status').annotate(models.Count('payment_status')):
            out[s['payment_status']] = s['payment_status__count']
        return out
    
    @cached_getter
    def payment_summary(self):
        finance = FinanceStatus()
        for ticket in self.ticket_set.all():
            finance.add_ticket(ticket)
        
        return finance
    
    class Meta:
        verbose_name = _('Topic')
        verbose_name_plural = _('Topics')
        ordering = ['-open_for_tickets', 'name']
        permissions = (
            ("supervisor", "Can edit all topics and tickets"),
        )

class Grant(models.Model):
    """ Grant is the bigger thing above topics """
    full_name = models.CharField(_('full name'), max_length=80, help_text=_('Full name for headlines and such'))
    short_name = models.CharField(_('short name'), max_length=16, help_text=_('Shorter name for use in tables'))
    slug = models.SlugField(_('slug'), help_text=_('Shortcut for usage in URLs'))
    description = models.TextField(_('description'), blank=True, help_text=_('Detailed description; HTML is allowed for now, line breaks are auto-parsed'))
    
    def __unicode__(self):
        return self.full_name
    
    def get_absolute_url(self):
        return reverse('grant_detail', kwargs={'slug':self.slug})
    
    class Meta:
        verbose_name = _('Grant')
        verbose_name_plural = _('Grants')
        ordering = ['full_name']


@receiver(comment_was_posted)
def ticket_note_comment(sender, comment, **kwargs):
    obj = comment.content_object 
    if type(obj) == Ticket:
        obj.save()

class MediaInfo(models.Model):
    """ Media related to particular tickets. """
    ticket = models.ForeignKey('tracker.Ticket', verbose_name=_('ticket'), help_text=_('Ticket this media info belongs to'))
    description = models.CharField(_('description'), max_length=255, help_text=_('Item description to show'))
    url = models.URLField(_('URL'), blank=True, help_text=_('Link to media files'))
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
    paid = models.BooleanField(_('paid'), default=False)
    wage = models.BooleanField(_('wage'), default=False)
    
    def __unicode__(self):
        return _('%(description)s (%(amount)s %(currency)s)') % {'description':self.description, 'amount':self.amount, 'currency':settings.TRACKER_CURRENCY}
    
    def save(self, *args, **kwargs):
        cluster_update_only = kwargs.pop('cluster_update_only', False)
        super(Expediture, self).save(*args, **kwargs)
        if not cluster_update_only and self.ticket.id != None:
            ClusterUpdate.perform(ticket_ids=set([self.ticket.id]))
    
    class Meta:
        verbose_name = _('Ticket expediture')
        verbose_name_plural = _('Ticket expeditures')

class Preexpediture(models.Model):
    """Preexpeditures related to particular tickets. """
    ticket = models.ForeignKey('tracker.Ticket', verbose_name=_('ticket'), help_text=_('Ticket this preexpediture belogns to'))
    description = models.CharField(_('description'), max_length=255, help_text=_('Description of this preexpediture'))
    amount = models.DecimalField(_('amount'), max_digits=8, decimal_places=2, help_text=string_concat(_('Preexpediture amount in'), ' ', settings.TRACKER_CURRENCY))

    def __unicode__(self):
        return _('%(description)s (%(amount)s %(currency)s)') % {'description':self.description, 'amount':self.amount, 'currency':settings.TRACKER_CURRENCY}

    def save(self, *args, **kwargs):
        cluster_update_only = kwargs.pop('cluster_update_only', False)
        super(Preexpediture, self).save(*args, **kwargs)
        if not cluster_update_only and self.ticket.id != None:
            ClusterUpdate.perform(ticket_ids=set([self.ticket.id]))

    class Meta:
        verbose_name = _('Ticket preexpediture')
        verbose_name_plural = _('Ticket preexpeditures')

# introductory chunk for the template
DOCUMENT_INTRO_TEMPLATE = template.Template('<a href="{% url "download_document" doc.ticket.id doc.filename %}">{{doc.filename}}</a>{% if detail and doc.description %}: {{doc.description}}{% endif %} <small>({{doc.content_type}}; {{doc.size|filesizeformat}})</small>')

class Document(models.Model):
    """ Document related to particular ticket, not publicly accessible. """
    ticket = models.ForeignKey('tracker.Ticket')
    filename = models.CharField(max_length=120, help_text='Document filename', validators=[
        RegexValidator(r'^[-_\.A-Za-z0-9]+\.[A-Za-z0-9]+$', message=_(u'We need a sane file name, such as my-invoice123.jpg')),
    ])
    size = models.PositiveIntegerField()
    content_type = models.CharField(max_length=64)
    description = models.CharField(max_length=255, blank=True, help_text='Optional further description of the document')
    payload = models.FileField(upload_to='tickets/%Y/', storage=FileSystemStorage(location=settings.TRACKER_DOCS_ROOT))
    
    def __unicode__(self):
        return self.filename
    
    def inline_intro(self):
        try:
            context = template.Context({'doc':self})
            return DOCUMENT_INTRO_TEMPLATE.render(context)
        except NoReverseMatch:
            return self.filename
    
    def html_item(self):
        context = template.Context({'doc':self, 'detail':True})
        return DOCUMENT_INTRO_TEMPLATE.render(context)
    
    class Meta:
        # by default, everyone can see and edit documents that belong to his tickets
        permissions = (
            ("see_all_docs", "Can see all documents"),
            ("edit_all_docs", "Can edit all documents"),
        )

from django.contrib.auth.models import User

class TrackerProfile(models.Model):
    user = models.OneToOneField(User)
    bank_account = models.CharField(_('Bank account'), max_length=120, blank=True, help_text=_('Bank account information for money transfers'))
    other_contact = models.CharField(_('Other contact'), max_length=120, blank=True, help_text=_('Other contact such as wiki account; can be useful in case of topic administrators need to clarify some information'))
    other_identification = models.CharField(_('Other identification'), max_length=120, blank=True, help_text=_('Address, or other identification information, so we know who are we sending money to'))
    
    def get_absolute_url(self):
        return reverse('user_detail', kwargs={'username':self.user.username})
    
    def media_count(self):
        return MediaInfo.objects.extra(where=['ticket_id in (select id from tracker_ticket where requested_user_id = %s)'], params=[self.user.id]).aggregate(objects=models.Count('id'), media=models.Sum('count'))
    
    def accepted_expeditures(self):
        return sum([t.accepted_expeditures() for t in self.user.ticket_set.filter(rating_percentage__gt=0)])
    
    def transactions(self):
        return Transaction.objects.filter(other=self.user).aggregate(count=models.Count('id'), amount=models.Sum('amount'))

@receiver(post_save, sender=User)
def create_user_profile(sender, **kwargs):
    if not kwargs.get('created', False):
        return
    
    user = kwargs['instance']
    profile = TrackerProfile.objects.create(user=user)

class Transaction(models.Model):
    """ One payment to or from the user. """
    date = models.DateField(_('date'))
    other = models.ForeignKey('auth.User', verbose_name=_('other party'), blank=True, null=True, help_text=_('The other party; user who sent or received the payment'))
    other_text = models.CharField(_('other party (text)'), max_length=60, blank=True, help_text=_('The other party; this text is used when user is not selected'))
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
    
    def other_party(self):
        if self.other != None:
            return self.other.username
        else:
            return self.other_text
    other_party.short_description = _('other party')
    
    def other_party_html(self):
        if self.other != None:
            return UserWrapper(self.other).get_html_link()
        else:
            return escape(self.other_text)
    
    def ticket_ids(self):
        return u', '.join([unicode(t.id) for t in self.tickets.order_by('id')])
    
    def tickets_by_id(self):
        return self.tickets.order_by('id')
    
    def grant_set(self):
        return Grant.objects.extra(where=['id in (select grant_id from tracker_topic topic where topic.id in (select topic_id from tracker_ticket ticket where ticket.id in (select ticket_id from tracker_transaction_tickets where transaction_id = %s)))'], params=[self.id]).order_by('id')
    
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

        if abs(paid - tickets) < 0.01: # float-friendly equality
            if tickets == 0:
                return 'n_a'
            else:
                return 'paid'
        elif paid < tickets:
            if paid == 0:
                return 'unpaid'
            else:
                return 'partially_paid'
        else: # paid > tickets
            return 'overpaid'
    
    def get_topic_count(self):
        """ Retuns number of topic this cluster spans """
        topic_set = set([t.topic_id for t in self.ticket_set.only('topic').select_related('topic')])
        return len(topic_set)
    
    def update_status(self):
        """ Recounts all the summaries and updates payment status in tickets. """
        self.total_tickets = sum([t.accepted_expeditures() for t in self.ticket_set.all()])
        self.total_transactions = self.transaction_set.all().aggregate(amount=models.Sum('amount'))['amount']
        status = self.get_status()
        for t in self.ticket_set.all():
            t.payment_status = status
            t.save(cluster_update_only=True)
        self.save()
    
    def __unicode__(self):
        return unicode(self.id)
    
    @staticmethod
    def cluster_sums():
        sums = {'unpaid':0, 'paid':0, 'overpaid':0}
        for cluster in Cluster.objects.all():
            tickets = cluster.total_tickets or 0
            transactions = cluster.total_transactions or 0
            if tickets == transactions:
                # paid
                sums['paid'] += tickets
            elif tickets > transactions:
                # unpaid or partially paid
                sums['paid'] += transactions
                sums['unpaid'] += tickets - transactions
            else:
                # overpaid
                sums['paid'] += tickets
                sums['overpaid'] += transactions - tickets
        return sums

@receiver(models.signals.m2m_changed)
def cluster_note_transaction_link(sender, instance, action, **kwargs):
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return
    
    if type(instance) == Transaction:
        ClusterUpdate.perform(transaction_ids=set([instance.id]))
    elif type(instance) == Ticket:
        ClusterUpdate.perform(ticket_ids=set([instance.id]))

@receiver(models.signals.pre_delete)
def cluster_member_delete(sender, instance, **kwargs):
    if sender == Transaction:
        instance.tickets.clear()
    elif sender == Ticket:
        instance.transaction_set.clear()
        
        # if previous clear produced a new cluster (which can happen for tickets, delete it)
        cluster_refreshed = Ticket.objects.get(id=instance.id).cluster
        if cluster_refreshed != None:
            cluster_refreshed.delete()


class TicketAck(models.Model):
    """ Ack flag for given ticket. """
    ticket = models.ForeignKey('Ticket')
    ack_type = models.CharField(max_length=20, choices=ACK_TYPES)
    added = models.DateTimeField(_('created'), auto_now_add=True)
    added_by = models.ForeignKey('auth.User', blank=True, null=True)
    comment = models.CharField(blank=True, max_length=255)
    
    def __unicode__(self):
        return u'%d %s by %s on %s' % (self.ticket_id, self.get_ack_type_display(), self.added_by, self.added)
    
    def added_by_html(self):
        if self.added_by != None:
            return UserWrapper(self.added_by).get_html_link()
        else:
            return ''
    
    @property
    def user_removable(self):
        """ If this ack can be removed by user (provided the ticket is not locked, user has rights, etc) """
        return self.ack_type in USER_EDITABLE_ACK_TYPES
    
    class Meta:
        ordering = ['added']

@receiver(post_save, sender=TicketAck)
def flush_ticket_after_ack_save(sender, instance, created, raw, **kwargs):
    if not raw:
        instance.ticket.flush_cache()
        ClusterUpdate.perform(ticket_ids=set([instance.ticket.id]))
        
@receiver(post_delete, sender=TicketAck)
def flush_ticket_after_ack_delete(sender, instance, **kwargs):
    instance.ticket.flush_cache()
    ClusterUpdate.perform(ticket_ids=set([instance.ticket.id]))

class PossibleAck(object):
    """ Python representation of possible ack that can be added by user to a ticket. """
    _display_names = dict(ACK_TYPES)
    
    def __init__(self, ack_type):
        if ack_type not in self._display_names:
            raise ValueError(ack_type)
        self.ack_type = ack_type
    
    def __eq__(self, other):
        return self.ack_type == other.ack_type
    
    def __unicode__(self):
        return self.display
    
    @property
    def display(self):
        return self._display_names[self.ack_type]
