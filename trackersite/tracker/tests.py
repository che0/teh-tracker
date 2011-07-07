# -*- coding: utf-8 -*-

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from tracker.models import Ticket, Topic, MediaInfo, Expediture

class SimpleTicketTest(TestCase):
    def setUp(self):
        self.topic = Topic(name='topic1')
        self.topic.save()
        
        self.ticket1 = Ticket(summary='foo', requested_by='req1', topic=self.topic, status='init', description='foo foo')
        self.ticket1.save()
        
        self.ticket2 = Ticket(summary='bar', requested_by='req2', topic=self.topic, status='init', description='bar bar')
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
    
    def test_topic_list(self):
        response = Client().get(reverse('topic_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['topic_list']), 1)
    
    def test_topic_detail(self):
        response = Client().get(reverse('topic_detail', kwargs={'pk':self.topic.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['topic'].ticket_set.all()), 2)
    
    def test_topic_absolute_url(self):
        t = self.topic
        self.assertEqual(reverse('topic_detail', kwargs={'pk':t.id}), t.get_absolute_url())

class TicketSumTests(TestCase):
    def setUp(self):
        self.topic = Topic(name='topic')
        self.topic.save()
        
    def test_empty_ticket(self):
        empty_ticket = Ticket(topic=self.topic, requested_by='someone', summary='empty ticket', status='x')
        empty_ticket.save()
        
        self.assertEqual(0, empty_ticket.media_count()['objects'])
        self.assertEqual(0, empty_ticket.expeditures()['count'])
    
    def test_full_ticket(self):
        full_ticket = Ticket(topic=self.topic, requested_by='someone', summary='full ticket', status='x', amount_paid=200)
        full_ticket.save()
        full_ticket.mediainfo_set.create(description='Vague pictures')
        full_ticket.mediainfo_set.create(description='Counted pictures', count=15)
        full_ticket.mediainfo_set.create(description='Even more pictures', count=16)
        full_ticket.expediture_set.create(description='Some expense', amount=99)
        full_ticket.expediture_set.create(description='Some other expense', amount=101)
        
        self.assertEqual({'objects': 3, 'media': 31}, full_ticket.media_count())
        self.assertEqual({'count': 2, 'amount': 200}, full_ticket.expeditures())

class TicketTests(TestCase):
    def setUp(self):
        self.open_topic = Topic(name='test_topic', open_for_tickets=True)
        self.open_topic.save()
        
        self.password = 'password'
        self.user = User(username='user')
        self.user.set_password(self.password)
        self.user.save()
    
    def get_client(self):
        c = Client()
        c.login(username=self.user.username, password=self.password)
        return c
    
    def test_ticket_creation_denied(self):
        response = Client().get(reverse('create_ticket'))
        self.assertEqual(302, response.status_code) # redirects to login
    
    def test_ticket_creation(self):
        c = self.get_client()
        response = c.get(reverse('create_ticket'))
        self.assertEqual(200, response.status_code)
        
        response = c.post(reverse('create_ticket'))
        self.assertEqual(200, response.status_code)
        self.assertFormError(response, 'form', 'summary', 'This field is required.')
        
        response = c.post(reverse('create_ticket'), {
                'summary': 'ticket',
                'topic': self.open_topic.id,
                'description': 'some desc',
            })
        self.assertEqual(1, Ticket.objects.count())
        ticket = Ticket.objects.order_by('-created')[0]
        self.assertEqual(self.user.username, ticket.requested_by)
        self.assertEqual('new', ticket.status)
        self.assertRedirects(response, reverse('ticket_detail', kwargs={'pk':ticket.id}))
    
    def test_wrong_topic_id(self):
        c = self.get_client()
        response = c.post(reverse('create_ticket'), {
                'summary': 'ticket',
                'topic': 'gogo',
                'description': 'some desc',
            })
        self.assertEqual(200, response.status_code)
        self.assertFormError(response, 'form', 'topic', 'Select a valid choice. That choice is not one of the available choices.')
    
    def test_closed_topic(self):
        closed_topic = Topic(name='closed topic', open_for_tickets=False)
        closed_topic.save()
        
        c = self.get_client()
        response = c.post(reverse('create_ticket'), {
                'summary': 'ticket',
                'topic': closed_topic.id,
                'description': 'some desc'
            })
        self.assertEqual(200, response.status_code)
        self.assertFormError(response, 'form', 'topic', 'Select a valid choice. That choice is not one of the available choices.')
