# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404

from tracker.models import Topic, Ticket, Transaction

class LatestTicketsFeed(Feed):
    description_template = 'feeds/ticket_description.html'
    title = _('Latest tickets')
    description = _('Recently changed tickets')

    def link(self):
        return reverse('ticket_list')
    
    def items(self):
        return Ticket.objects.order_by('-updated')[:10]
    
    def item_pubdate(self, item):
        return item.updated

class SubmittedTicketsFeed(LatestTicketsFeed):
    title = _('Latest submitted tickets')
    description = _('Recently changed submitted tickets')
    
    def items(self):
        return [t for t in Ticket.objects.order_by('-updated')[:40] if t.has_ack('user_content')]

class TopicTicketsFeed(Feed):
    description_template = 'feeds/ticket_description.html'
    
    def get_object(self, request, pk):
        return get_object_or_404(Topic, id=pk)
    
    def title(self, topic):
        return unicode(topic)
    
    def link(self, topic):
        return topic.get_absolute_url()
    
    def items(self, topic):
        return topic.ticket_set.order_by('-updated')[:10]
    
    def item_pubdate(self, item):
        return item.updated

class TopicSubmittedTicketsFeed(TopicTicketsFeed):
    def items(self, topic):
        return [t for t in topic.ticket_set.order_by('-updated')[:40] if t.has_ack('user_content')]

class TransactionsFeed(Feed):
    description_template = 'feeds/transaction_description.html'
    
    def link(self):
        return reverse('transaction_list')
    
    def items(self):
        return Transaction.objects.order_by('-date')[:10]
    
    def item_link(self, item):
        return item.other.get_absolute_url()
    
    def item_guid(self, item):
        return '2011/11/trans/%s' % item.id
