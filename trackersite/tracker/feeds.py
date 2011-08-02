# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404

from tracker.models import Topic, Ticket

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
