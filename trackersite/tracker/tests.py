# -*- coding: utf-8 -*-

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

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
    
    def test_ticket_absolute_url(self):
        t = self.ticket1
        self.assertEqual(reverse('ticket_detail', kwargs={'pk':t.id}), t.get_absolute_url())
    
class TicketTests(TestCase):
    def setUp(self):
        self.password = 'password'
        self.user = User(username='user')
        self.user.set_password(self.password)
        self.user.save()
    
    def test_ticket_creation_denied(self):
        response = Client().get(reverse('create_ticket'))
        self.assertEqual(302, response.status_code) # redirects to login
    
    def test_ticket_creation(self):
        c = Client()
        c.login(username=self.user.username, password=self.password)
        response = c.get(reverse('create_ticket'))
        self.assertEqual(200, response.status_code)
        
        response = c.post(reverse('create_ticket'))
        self.assertEqual(200, response.status_code)
        
        response = c.post(reverse('create_ticket'), {
                'summary': 'ticket',
                'topic': 'some topic',
                'status': 'new',
                'description': 'some desc',
            })
        self.assertEqual(1, Ticket.objects.count())
        ticket = Ticket.objects.order_by('-created')[0]
        self.assertEqual(self.user.username, ticket.requested_by)
        self.assertRedirects(response, reverse('ticket_detail', kwargs={'pk':ticket.id}))
