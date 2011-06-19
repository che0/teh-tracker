# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from django.views.generic import ListView, DetailView

from tracker.models import Ticket

urlpatterns = patterns('',
    url(r'^$', ListView.as_view(model=Ticket), name='ticket_list'),
    url(r'^ticket/(?P<pk>\d+)/$', DetailView.as_view(model=Ticket), name='ticket_detail'),
    url(r'^ticket/new/$', 'tracker.views.create_ticket', name='create_ticket'),
    url(r'^comments/', include('django.contrib.comments.urls')),
)
