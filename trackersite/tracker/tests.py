# -*- coding: utf-8 -*-
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from tracker.models import Ticket

class SimpleTicketTest(TestCase):
    def setUp(self):
        self.ticket1 = Ticket(summary='foo', requested_by='req1', topic='t1', status='init', description='foo foo')
        self.ticket1.save()
        
        self.ticket2 = Ticket(summary='bar', requested_by='req2', topic='t2', status='init', description='bar bar')
        self.ticket2.save()
    
    def test_ticket_timestamps(self):
        self.assertTrue(self.ticket2.created > self.ticket1.created) # check ticket 2 is newer
        
        # check new update of ticket changed updated ts
        old_updated = self.ticket1.updated
        self.ticket1.description = 'updated description'
        self.ticket1.save()
        self.assertTrue(self.ticket1.updated > old_updated)
    
    def test_ticket_list(self):
        response = Client().get(reverse('ticket_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['ticket_list']), 2)

    def test_ticket_detail(self):
        response = Client().get(reverse('ticket_detail', kwargs={'pk':self.ticket1.id}))
        self.assertEqual(response.status_code, 200)
    
    def test_ticket_url_escape(self):
        url = 'http://meta.wikimedia.org/wiki/Mediagrant/Fotografie_um%C4%9Bleck%C3%BDch_pam%C3%A1tek_v_%C4%8Cesk%C3%A9m_Krumlov%C4%9B'
        self.ticket1.description = '<a href="%s">foo link</a>' % url
        self.ticket1.save()
        response = Client().get(reverse('ticket_detail', kwargs={'pk':self.ticket1.id}))
        self.assertContains(response, 'href="%s"' % url, 1)
