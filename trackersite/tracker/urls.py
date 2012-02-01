# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from django.views.generic import ListView, RedirectView

from tracker.models import Ticket, Topic
from tracker.feeds import LatestTicketsFeed, TopicTicketsFeed, TransactionsFeed

urlpatterns = patterns('',
    url(r'^tickets/$', ListView.as_view(model=Ticket), name='ticket_list'),
    url(r'^tickets/feed/$', LatestTicketsFeed(), name='ticket_list_feed'),
    url(r'^ticket/(?P<pk>\d+)/$', 'tracker.views.ticket_detail', name='ticket_detail'),
    url(r'^ticket/(?P<pk>\d+)/edit/$', 'tracker.views.edit_ticket', name='edit_ticket'),
    url(r'^ticket/new/$', 'tracker.views.create_ticket', name='create_ticket'),
    url(r'^topics/$', ListView.as_view(model=Topic), name='topic_list'),
    url(r'^topic/(?P<pk>\d+)/$', 'tracker.views.topic_detail', name='topic_detail'),
    url(r'^topic/(?P<pk>\d+)/feed/$', TopicTicketsFeed(), name='topic_ticket_feed'),
    url(r'^users/$', 'tracker.views.user_list', name='user_list'),
    url(r'^users/(?P<username>[^/]+)/$', 'tracker.views.user_detail', name='user_detail'),
    url(r'^transactions/$', 'tracker.views.transaction_list', name='transaction_list'),
    url(r'^transactions/feed/$', TransactionsFeed(), name='transactions_feed'),
    url(r'^cluster/(?P<pk>\d+)/$', 'tracker.views.cluster_detail', name='cluster_detail'),
    url(r'^comments/', include('django.contrib.comments.urls')),
    url(r'^old/(?P<url>(?:tickets?/|topics?/|)(?:\d+/|new/)?)$', RedirectView.as_view(url='/%(url)s')),
    url(r'^js/topics\.js$', 'tracker.views.topics_js', name='topics_js'),
)
