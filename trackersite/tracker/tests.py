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
        
        self.ticket1 = Ticket(summary='foo', requested_text='req1', topic=self.topic, state='for consideration', description='foo foo')
        self.ticket1.save()
        
        self.ticket2 = Ticket(summary='bar', requested_text='req2', topic=self.topic, state='for consideration', description='bar bar')
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
    
    def test_javascript_topic_list(self):
        response = Client().get(reverse('topics_js'))
        self.assertEqual(response.status_code, 200)
    
    def test_topic_detail(self):
        response = Client().get(reverse('topic_detail', kwargs={'pk':self.topic.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['topic'].ticket_set.all()), 2)
    
    def test_topic_absolute_url(self):
        t = self.topic
        self.assertEqual(reverse('topic_detail', kwargs={'pk':t.id}), t.get_absolute_url())

class OldRedirectTests(TestCase):
    def setUp(self):
        self.topic = Topic(name='topic')
        self.topic.save()
        self.ticket = Ticket(summary='foo', requested_text='req', topic=self.topic, state='for consideration', description='foo foo')
        self.ticket.save()
    
    def assert301(self, *args, **kwargs):
        kwargs['status_code'] = 301
        self.assertRedirects(*args, **kwargs)
    
    def test_old_index(self):
        response = Client().get('/old/')
        self.assert301(response, '/', target_status_code=302) # 302 = now index is a non-permanent redirect
    
    def test_topic_index(self):
        response = Client().get('/old/topics/')
        self.assert301(response, reverse('topic_list'))
    
    def test_ticket(self):
        response = Client().get('/old/ticket/%s/' % self.ticket.id)
        self.assert301(response, self.ticket.get_absolute_url())
    
    def test_new_ticket(self):
        response = Client().get('/old/ticket/new/')
        self.assert301(response, reverse('create_ticket'), target_status_code=302) # 302 = redirect to login
    
    def test_topic(self):
        response = Client().get('/old/topic/%s/' % self.topic.id)
        self.assert301(response, self.topic.get_absolute_url())

class TicketSumTests(TestCase):
    def setUp(self):
        self.topic = Topic(name='topic')
        self.topic.save()
        
    def test_empty_ticket(self):
        empty_ticket = Ticket(topic=self.topic, requested_text='someone', summary='empty ticket', state='for consideration')
        empty_ticket.save()
        
        self.assertEqual(0, empty_ticket.media_count()['objects'])
        self.assertEqual(0, empty_ticket.expeditures()['count'])
        self.assertEqual(0, self.topic.media_count()['objects'])
        self.assertEqual(0, self.topic.expeditures()['count'])
    
    def test_full_ticket(self):
        full_ticket = Ticket(topic=self.topic, requested_text='someone', summary='full ticket', state='for consideration')
        full_ticket.save()
        full_ticket.mediainfo_set.create(description='Vague pictures')
        full_ticket.mediainfo_set.create(description='Counted pictures', count=15)
        full_ticket.mediainfo_set.create(description='Even more pictures', count=16)
        full_ticket.expediture_set.create(description='Some expense', amount=99)
        full_ticket.expediture_set.create(description='Some other expense', amount=101)
        
        self.assertEqual({'objects': 3, 'media': 31}, full_ticket.media_count())
        self.assertEqual({'count': 2, 'amount': 200}, full_ticket.expeditures())
        self.assertEqual({'objects': 3, 'media': 31}, self.topic.media_count())
        self.assertEqual({'count': 2, 'amount': 200}, self.topic.expeditures())

class TicketTests(TestCase):
    def setUp(self):
        self.open_topic = Topic(name='test_topic', open_for_tickets=True, ticket_media=True)
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
        self.assertEqual(400, response.status_code)
        
        response = c.post(reverse('create_ticket'), {
                'mediainfo-INITIAL_FORMS': '0',
                'mediainfo-TOTAL_FORMS': '0',
                'expediture-INITIAL_FORMS': '0',
                'expediture-TOTAL_FORMS': '0',
            })
        self.assertEqual(200, response.status_code)
        self.assertFormError(response, 'ticketform', 'summary', 'This field is required.')
        
        response = c.post(reverse('create_ticket'), {
                'summary': 'ticket',
                'topic': self.open_topic.id,
                'description': 'some desc',
                'mediainfo-INITIAL_FORMS': '0',
                'mediainfo-TOTAL_FORMS': '0',
                'expediture-INITIAL_FORMS': '0',
                'expediture-TOTAL_FORMS': '0',
            })
        self.assertEqual(1, Ticket.objects.count())
        ticket = Ticket.objects.order_by('-created')[0]
        self.assertEqual(self.user, ticket.requested_user)
        self.assertEqual(self.user.username, ticket.requested_by())
        self.assertEqual('for consideration', ticket.state)
        self.assertRedirects(response, reverse('ticket_detail', kwargs={'pk':ticket.id}))
    
    def test_ticket_creation_with_media(self):
        c = self.get_client()
        response = c.post(reverse('create_ticket'), {
                'summary': 'ticket',
                'topic': self.open_topic.id,
                'description': 'some desc',
                'mediainfo-INITIAL_FORMS': '0',
                'mediainfo-TOTAL_FORMS': '3',
                'mediainfo-0-count': '',
                'mediainfo-0-description': 'image 1',
                'mediainfo-0-url': 'http://www.example.com/image1.jpg',
                'mediainfo-1-count': '',
                'mediainfo-1-description': '', 
                'mediainfo-1-url': '',
                'mediainfo-2-count': '3',
                'mediainfo-2-description': 'image 2 - group',
                'mediainfo-2-url': 'http://www.example.com/imagegroup/',
                'expediture-INITIAL_FORMS': '0',
                'expediture-TOTAL_FORMS': '0',
            })
        self.assertEqual(1, Ticket.objects.count())
        ticket = Ticket.objects.order_by('-created')[0]
        
        media = ticket.mediainfo_set.order_by('description')
        self.assertEqual(2, len(media))
        self.assertEqual('image 1', media[0].description)
        self.assertEqual('http://www.example.com/image1.jpg', media[0].url)
        self.assertEqual(None, media[0].count)
        self.assertEqual('image 2 - group', media[1].description)
        self.assertEqual('http://www.example.com/imagegroup/', media[1].url)
        self.assertEqual(3, media[1].count)
    
    def test_wrong_topic_id(self):
        c = self.get_client()
        response = c.post(reverse('create_ticket'), {
                'summary': 'ticket',
                'topic': 'gogo',
                'description': 'some desc',
                'mediainfo-INITIAL_FORMS': '0',
                'mediainfo-TOTAL_FORMS': '0',
                'expediture-INITIAL_FORMS': '0',
                'expediture-TOTAL_FORMS': '0',
            })
        self.assertEqual(200, response.status_code)
        self.assertFormError(response, 'ticketform', 'topic', 'Select a valid choice. That choice is not one of the available choices.')
    
    def test_closed_topic(self):
        closed_topic = Topic(name='closed topic', open_for_tickets=False)
        closed_topic.save()
        
        c = self.get_client()
        response = c.post(reverse('create_ticket'), {
                'summary': 'ticket',
                'topic': closed_topic.id,
                'description': 'some desc',
                'mediainfo-INITIAL_FORMS': '0',
                'mediainfo-TOTAL_FORMS': '0',
                'expediture-INITIAL_FORMS': '0',
                'expediture-TOTAL_FORMS': '0',
            })
        self.assertEqual(200, response.status_code)
        self.assertFormError(response, 'ticketform', 'topic', 'Select a valid choice. That choice is not one of the available choices.')

class TicketEditTests(TestCase):
    def test_correct_choices(self):
        t_closed = Topic(name='t1', open_for_tickets=False)
        t_closed.save()
        t_open = Topic(name='t2', open_for_tickets=True)
        t_open.save()
        t_assigned = Topic(name='t3', open_for_tickets=False)
        t_assigned.save()
        ticket = Ticket(summary='ticket', topic=t_assigned)
        ticket.save()
        
        from tracker.views import get_edit_ticket_form_class
        EditForm = get_edit_ticket_form_class(ticket)
        choices = {t.id for t in EditForm().fields['topic'].queryset.all()}
        wanted_choices = {t_open.id, t_assigned.id}
        self.assertEqual(wanted_choices, choices)
    
    def test_ticket_edit(self):
        topic = Topic(name='topic')
        topic.save()
        
        password = 'my_password'
        user = User(username='my_user')
        user.set_password(password)
        user.save()
        
        ticket = Ticket(summary='ticket', topic=topic, requested_user=None, requested_text='foo', state='closed')
        ticket.save()
        
        c = Client()
        response = c.get(reverse('edit_ticket', kwargs={'pk':ticket.id}))
        self.assertEqual(302, response.status_code) # should be redirect to login page
        
        c.login(username=user.username, password=password)
        response = c.get(reverse('edit_ticket', kwargs={'pk':ticket.id}))
        self.assertEqual(403, response.status_code) # denies edit of non-own ticket
        
        ticket.requested_user = user
        ticket.requested_text = ''
        ticket.save()
        response = c.get(reverse('edit_ticket', kwargs={'pk':ticket.id}))
        self.assertEqual(403, response.status_code) # still deny edit, ticket locked
        
        ticket.state = 'for consideration'
        ticket.save()
        response = c.get(reverse('edit_ticket', kwargs={'pk':ticket.id}))
        self.assertEqual(200, response.status_code) # now it should pass
        
        # try to submit the form
        response = c.post(reverse('edit_ticket', kwargs={'pk':ticket.id}), {
                'summary': 'new summary',
                'topic': ticket.topic.id,
                'description': 'new desc',
                'mediainfo-INITIAL_FORMS': '0',
                'mediainfo-TOTAL_FORMS': '0',
                'expediture-INITIAL_FORMS': '0',
                'expediture-TOTAL_FORMS': '0',
            })
        self.assertRedirects(response, reverse('ticket_detail', kwargs={'pk':ticket.id}))
        
        # check changed ticket data
        ticket = Ticket.objects.get(id=ticket.id)
        self.assertEqual(user, ticket.requested_user)
        self.assertEqual('new summary', ticket.summary)
        self.assertEqual('new desc', ticket.description)
        
        # b0rked media item aborts the submit
        response = c.post(reverse('edit_ticket', kwargs={'pk':ticket.id}), {
                'summary': 'ticket',
                'topic': ticket.topic.id,
                'description': 'some desc',
                'mediainfo-INITIAL_FORMS': '0',
                'mediainfo-TOTAL_FORMS': '1',
                'mediainfo-0-count': 'foo',
                'mediainfo-0-description': 'image 1',
                'mediainfo-0-url': 'http://www.example.com/image1.jpg',
                'expediture-INITIAL_FORMS': '0',
                'expediture-TOTAL_FORMS': '0',
            })
        self.assertEqual(200, response.status_code)
        self.assertEqual('Enter a whole number.', response.context['mediainfo'].forms[0].errors['count'][0])
        
        # b0rked expediture items aborts the submit
        response = c.post(reverse('edit_ticket', kwargs={'pk':ticket.id}), {
                'summary': 'ticket',
                'topic': ticket.topic.id,
                'description': 'some desc',
                'mediainfo-INITIAL_FORMS': '0',
                'mediainfo-TOTAL_FORMS': '0',
                'expediture-INITIAL_FORMS': '0',
                'expediture-TOTAL_FORMS': '1',
                'expediture-0-description': 'foo',
                'expediture-0-amount': '',
            })
        self.assertEqual(200, response.status_code)
        self.assertEqual('This field is required.', response.context['expeditures'].forms[0].errors['amount'][0])
        
        # add some inline items
        response = c.post(reverse('edit_ticket', kwargs={'pk':ticket.id}), {
                'summary': 'new summary',
                'topic': ticket.topic.id,
                'description': 'new desc',
                'mediainfo-INITIAL_FORMS': '0',
                'mediainfo-TOTAL_FORMS': '3',
                'mediainfo-0-count': '',
                'mediainfo-0-description': 'image 1',
                'mediainfo-0-url': 'http://www.example.com/image1.jpg',
                'mediainfo-1-count': '',
                'mediainfo-1-description': '', 
                'mediainfo-1-url': '',
                'mediainfo-2-count': '3',
                'mediainfo-2-description': 'image 2 - group',
                'mediainfo-2-url': 'http://www.example.com/imagegroup/',
                'expediture-INITIAL_FORMS': '0',
                'expediture-TOTAL_FORMS': '2',
                'expediture-0-description': 'ten fifty',
                'expediture-0-amount': '10.50',
                'expediture-1-description': 'hundred',
                'expediture-1-amount': '100',
            })
        self.assertRedirects(response, reverse('ticket_detail', kwargs={'pk':ticket.id}))
        media = ticket.mediainfo_set.order_by('description')
        self.assertEqual(2, len(media))
        self.assertEqual('image 1', media[0].description)
        self.assertEqual('http://www.example.com/image1.jpg', media[0].url)
        self.assertEqual(None, media[0].count)
        self.assertEqual('image 2 - group', media[1].description)
        self.assertEqual('http://www.example.com/imagegroup/', media[1].url)
        self.assertEqual(3, media[1].count)
        expeditures = ticket.expediture_set.order_by('amount')
        self.assertEqual(2, len(expeditures))
        self.assertEqual('ten fifty', expeditures[0].description)
        self.assertEqual(10.5, expeditures[0].amount)
        self.assertEqual('hundred', expeditures[1].description)
        self.assertEqual(100, expeditures[1].amount)
        
        # edit inline items
        response = c.post(reverse('edit_ticket', kwargs={'pk':ticket.id}), {
                'summary': 'new summary',
                'topic': ticket.topic.id,
                'description': 'new desc',
                'mediainfo-INITIAL_FORMS': '2',
                'mediainfo-TOTAL_FORMS': '3',
                'mediainfo-0-id': media[0].id,
                'mediainfo-0-count': '1',
                'mediainfo-0-description': 'image 1 - edited',
                'mediainfo-0-url': 'http://www.example.com/second.jpg',
                'mediainfo-1-id': media[1].id,
                'mediainfo-1-DELETE': 'on',
                'mediainfo-1-count': '3',
                'mediainfo-1-description': 'image 2 - group',
                'mediainfo-1-url': 'http://www.example.com/imagegroup/',
                'mediainfo-2-count': '',
                'mediainfo-2-description': '', 
                'mediainfo-2-url': '',
                'expediture-INITIAL_FORMS': '2',
                'expediture-TOTAL_FORMS': '3',
                'expediture-0-id': expeditures[0].id,
                'expediture-0-description': 'ten fifty',
                'expediture-0-amount': '10.50',
                'expediture-0-DELETE': 'on',
                'expediture-1-id': expeditures[1].id,
                'expediture-1-description': 'hundred+1',
                'expediture-1-amount': '101',
                'expediture-2-description': '',
                'expediture-2-amount': '',
            })
        self.assertRedirects(response, reverse('ticket_detail', kwargs={'pk':ticket.id}))
        media = ticket.mediainfo_set.all()
        self.assertEqual(1, len(media))
        self.assertEqual('image 1 - edited', media[0].description)
        self.assertEqual('http://www.example.com/second.jpg', media[0].url)
        self.assertEqual(1, media[0].count)
        expeditures = ticket.expediture_set.order_by('amount')
        self.assertEqual(1, len(expeditures))
        self.assertEqual('hundred+1', expeditures[0].description)
        self.assertEqual(101, expeditures[0].amount)
