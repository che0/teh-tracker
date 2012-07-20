# -*- coding: utf-8 -*-

import datetime

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Permission, SiteProfileNotAvailable
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.conf import settings

from tracker.models import Ticket, Topic, Grant, MediaInfo, Expediture, Transaction, UserProfile, Document, Cluster

class SimpleTicketTest(TestCase):
    def setUp(self):
        self.topic = Topic(name='topic1', grant=Grant.objects.create(full_name='g', short_name='g'))
        self.topic.save()
        
        self.ticket1 = Ticket(summary='foo', requested_text='req1', topic=self.topic, state='for consideration', description='foo foo')
        self.ticket1.save()
        
        self.ticket2 = Ticket(summary='bar', requested_text='req2', topic=self.topic, state='for consideration', description='bar bar')
        self.ticket2.save()
    
    def test_ticket_sort_date(self):
        # sort date is equal to event date (when applicable) and default to creation date
        self.assertEqual(self.ticket1.created.date(), self.ticket1.sort_date)
        
        self.ticket1.event_date = datetime.date(2011, 10, 13)
        self.ticket1.save()
        self.assertEqual(datetime.date(2011, 10, 13), self.ticket1.sort_date)
        
        self.ticket1.event_date = None
        self.ticket1.save()
        self.assertEqual(self.ticket1.created.date(), self.ticket1.sort_date)
    
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
        self.topic = Topic(name='topic', grant=Grant.objects.create(full_name='g', short_name='g'))
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
        self.topic = Topic(name='topic', grant=Grant.objects.create(full_name='g', short_name='g'))
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
        self.open_topic = Topic(name='test_topic', open_for_tickets=True, ticket_media=True, grant=Grant.objects.create(full_name='g', short_name='g'))
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
        self.assertEqual(302, response.status_code)
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
        self.assertEqual(302, response.status_code)
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
        closed_topic = Topic(name='closed topic', open_for_tickets=False, grant=Grant.objects.create(full_name='g', short_name='g'))
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
        grant = Grant.objects.create(full_name='g', short_name='g')
        t_closed = Topic(name='t1', open_for_tickets=False, grant=grant)
        t_closed.save()
        t_open = Topic(name='t2', open_for_tickets=True, grant=grant)
        t_open.save()
        t_assigned = Topic(name='t3', open_for_tickets=False, grant=grant)
        t_assigned.save()
        ticket = Ticket(summary='ticket', topic=t_assigned)
        ticket.save()
        
        from tracker.views import get_edit_ticket_form_class
        EditForm = get_edit_ticket_form_class(ticket)
        choices = {t.id for t in EditForm().fields['topic'].queryset.all()}
        wanted_choices = {t_open.id, t_assigned.id}
        self.assertEqual(wanted_choices, choices)
    
    def test_ticket_edit(self):
        topic = Topic(name='topic', grant=Grant.objects.create(full_name='g', short_name='g'))
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
    
class TicketEditLinkTests(TestCase):
    def setUp(self):
        self.topic = Topic(name='topic', grant=Grant.objects.create(full_name='g', short_name='g'))
        self.topic.save()
        
        self.password = 'my_password'
        self.user = User(username='my_user')
        self.user.set_password(self.password)
        self.user.save()
        
        self.ticket = Ticket(summary='ticket', topic=self.topic, requested_user=None, requested_text='foo', state='for consideration')
        self.ticket.save()
    
    def get_ticket_response(self):
        c = Client()
        c.login(username=self.user.username, password=self.password)
        response = c.get(reverse('ticket_detail', kwargs={'pk':self.ticket.id}))
        self.assertEqual(response.status_code, 200)
        return response
    
    def test_clear_ticket(self):
        response = self.get_ticket_response()
        self.assertEqual(False, response.context['user_can_edit_ticket'])
        self.assertEqual(False, response.context['user_can_edit_ticket_in_admin'])
        
    def test_own_ticket(self):
        self.ticket.requested_user = self.user
        self.ticket.save()
        response = self.get_ticket_response()
        self.assertEqual(True, response.context['user_can_edit_ticket'])
        self.assertEqual(False, response.context['user_can_edit_ticket_in_admin'])
    
    def test_bare_admin(self):
        self.user.is_staff = True
        self.user.save()
        response = self.get_ticket_response()
        self.assertEqual(False, response.context['user_can_edit_ticket'])
        self.assertEqual(False, response.context['user_can_edit_ticket_in_admin'])
    
    def test_tracker_supervisor(self):
        self.user.is_staff = True
        topic_content = ContentType.objects.get(app_label='tracker', model='Topic')
        self.user.user_permissions.add(Permission.objects.get(content_type=topic_content, codename='supervisor'))
        self.user.save()
        
        response = self.get_ticket_response()
        self.assertEqual(False, response.context['user_can_edit_ticket'])
        self.assertEqual(True, response.context['user_can_edit_ticket_in_admin'])
        
    def test_total_supervisor(self):
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        
        response = self.get_ticket_response()
        self.assertEqual(False, response.context['user_can_edit_ticket'])
        self.assertEqual(True, response.context['user_can_edit_ticket_in_admin'])
    
    def test_own_topic(self):
        self.user.is_staff = True
        self.user.topic_set.add(self.topic)
        self.user.save()
        
        response = self.get_ticket_response()
        self.assertEqual(False, response.context['user_can_edit_ticket'])
        self.assertEqual(True, response.context['user_can_edit_ticket_in_admin'])

class UserDetailsTest(TestCase):
    def setUp(self):
        self.topic = Topic(name='test_topic', open_for_tickets=True, ticket_media=True, grant=Grant.objects.create(full_name='g', short_name='g'))
        self.topic.save()
        
        self.user = User(username='user')
        self.user.save()
        
        self.ticket = Ticket(summary='foo', requested_user=self.user, topic=self.topic, state='for consideration', description='foo foo')
        self.ticket.save()
    
    def test_user_details(self):
        c = Client()
        response = c.get(self.user.get_absolute_url())
        self.assertEqual(200, response.status_code)
        self.assertEqual(self.ticket, response.context['ticket_list'][0])

class SummaryTest(TestCase):
    def setUp(self):
        self.user = User(username='user')
        self.user.save()
        
        self.topic = Topic(name='test_topic', ticket_expenses=True, grant=Grant.objects.create(full_name='g', short_name='g'))
        self.topic.save()
        
        self.ticket = Ticket(summary='foo', requested_user=self.user, topic=self.topic, state='expenses filed', rating_percentage=50)
        self.ticket.save()
        self.ticket.expediture_set.create(description='foo', amount=200)
        self.ticket.expediture_set.create(description='foo', amount=100)
        self.ticket.mediainfo_set.create(description='foo', count=5)
        
        self.ticket2 = Ticket(summary='foo', requested_user=self.user, topic=self.topic, state='expenses filed', rating_percentage=100)
        self.ticket2.save()
        self.ticket2.expediture_set.create(description='foo', amount=600)
        self.ticket2.expediture_set.create(description='foo', amount=10)
        self.ticket2.mediainfo_set.create(description='foo', count=5)
        self.ticket2.mediainfo_set.create(description='foo', count=3)
    
    def test_topic_ticket_counts(self):
        self.assertEqual({'unpaid':2}, self.topic.tickets_per_payment_status())
        trans = Transaction.objects.create(date=datetime.date.today(), other=self.user, amount=150)
        trans.tickets.add(self.ticket)
        self.assertEqual({'unpaid':1, 'paid':1}, self.topic.tickets_per_payment_status())

    def test_ticket_summary(self):
        self.ticket.state = 'for consideration'
        self.ticket.rating_percentage = None
        self.ticket.save()
        
        self.assertEqual({'objects':1, 'media':5}, self.ticket.media_count())
        self.assertEqual({'count':2, 'amount':300}, self.ticket.expeditures())
        self.assertEqual(0, self.ticket.accepted_expeditures())
        
        self.ticket.rating_percentage = 50
        self.ticket.save()
        self.assertEqual(0, self.ticket.accepted_expeditures())
        
        self.ticket.state = 'expenses filed'
        self.ticket.save()
        self.assertEqual(150, self.ticket.accepted_expeditures())

    def test_topic_summary(self):
        self.assertEqual({'objects':3, 'media':13}, self.topic.media_count())
        self.assertEqual({'count':4, 'amount':910}, self.topic.expeditures())
        self.assertEqual(150 + 610, self.topic.accepted_expeditures())
    
    def test_user_summary(self):
        profile = self.user.get_profile()
        self.assertEqual({'objects':3, 'media':13}, profile.media_count())
        self.assertEqual(150 + 610, profile.accepted_expeditures())
        self.assertEqual({'count':0, 'amount':None}, profile.transactions())
    
    def test_transaction_summary(self):
        def add_trans(amount):
            self.user.transaction_set.create(date=datetime.date.today(), amount=amount, description='foo')
        
        add_trans(500)
        self.assertEqual({'count':1, 'amount':500}, self.user.get_profile().transactions())

class TransactionTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create(username='user')
        self.tr = Transaction.objects.create(date=datetime.date(2011, 12, 24), amount=500, other=self.user, description='some desc')
        
        # more transactions
        tr2 = Transaction.objects.create(date=datetime.date(2011, 12, 25), amount=-200, other=self.user, description='other')
        self.user2 = User.objects.create(username='user2')
        Transaction.objects.create(date=datetime.date(2011, 12, 26), amount=300, other=self.user2, description='user2')
    
    def test_transaction_string(self):        
        self.assertEqual(u"%s, 500 %s: some desc" % (self.tr.date, settings.TRACKER_CURRENCY), unicode(self.tr))
    
    def test_transaction_list(self):
        c = Client()
        response = c.get(reverse('transaction_list'))
        self.assertEqual(200, response.status_code)
        self.assertEqual(600, response.context['total'])
    
    def test_user_list(self):
        topic = Topic.objects.create(name='test_topic', ticket_expenses=True, grant=Grant.objects.create(full_name='g', short_name='g'))
        ticket = Ticket.objects.create(summary='foo', requested_user=self.user2, topic=topic, state='expenses filed', rating_percentage=100)
        ticket.expediture_set.create(description='exp', amount=300)
        ticket.mediainfo_set.create(description='media', count=5)
        
        unt = Ticket.objects.create(summary='anon', topic=topic, state='custom')
        unt.mediainfo_set.create(description='media', count=3)
        
        c = Client()
        response = c.get(reverse('user_list'))
        self.assertEqual(200, response.status_code)
        
        expected_totals = {
            'ticket_count': 2,
            'media': {'objects':2, 'media':8},
            'accepted_expeditures': 300,
            'transactions': 600,
        }
        self.assertEqual(expected_totals, response.context['totals'])
        
        expected_unassigned = {
            'ticket_count': 1,
            'media': {'objects':1, 'media':3},
            'accepted_expeditures': 0,
        }
        self.assertEqual(expected_unassigned, response.context['unassigned'])

class ClusterTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='user')
        self.topic = Topic.objects.create(name='test_topic', ticket_expenses=True, grant=Grant.objects.create(full_name='g', short_name='g'))
        
    
    def test_simple_ticket(self):
        ticket = Ticket.objects.create(summary='foo', topic=self.topic, state='accepted', rating_percentage=100)
        tid = ticket.id
        self.assertEqual('n_a', Ticket.objects.get(id=tid).payment_status)
        
        ticket.state = 'expenses filed'
        ticket.save()
        self.assertEqual('n_a', Ticket.objects.get(id=tid).payment_status)
        self.assertEqual({'fuzzy':False, 'unpaid':0, 'paid':0, 'overpaid':0}, self.topic.payment_summary())
        self.assertEqual({'unpaid':0, 'paid':0, 'overpaid':0}, Cluster.cluster_sums())
        
        Expediture.objects.create(ticket_id=tid, description='exp', amount=100)
        self.assertEqual('unpaid', Ticket.objects.get(id=tid).payment_status)
        self.assertEqual({'fuzzy':False, 'unpaid':100, 'paid':0, 'overpaid':0}, self.topic.payment_summary())
        self.assertEqual({'unpaid':100, 'paid':0, 'overpaid':0}, Cluster.cluster_sums())
        
        tr = Transaction.objects.create(date=datetime.date(2011, 12, 24), amount=50, other=self.user, description='part one')
        tr.tickets.add(ticket)
        self.assertEqual('partially_paid', Ticket.objects.get(id=tid).payment_status)
        self.assertEqual({'fuzzy':False, 'unpaid':50, 'paid':50, 'overpaid':0}, self.topic.payment_summary())
        self.assertEqual({'unpaid':50, 'paid':50, 'overpaid':0}, Cluster.cluster_sums())
        
        tr = Transaction.objects.create(date=datetime.date(2011, 12, 25), amount=50, other=self.user, description='part one')
        tr.tickets.add(ticket)
        self.assertEqual('paid', Ticket.objects.get(id=tid).payment_status)
        self.assertEqual({'fuzzy':False, 'unpaid':0, 'paid':100, 'overpaid':0}, self.topic.payment_summary())
        self.assertEqual({'unpaid':0, 'paid':100, 'overpaid':0}, Cluster.cluster_sums())
        
        tr = Transaction.objects.create(date=datetime.date(2011, 12, 26), amount=50, other=self.user, description='overkill')
        tr.tickets.add(ticket)
        self.assertEqual('overpaid', Ticket.objects.get(id=tid).payment_status)
        self.assertEqual({'fuzzy':False, 'unpaid':0, 'paid':100, 'overpaid':50}, self.topic.payment_summary())
        self.assertEqual({'unpaid':0, 'paid':100, 'overpaid':50}, Cluster.cluster_sums())
        
        c = Ticket.objects.get(id=tid).cluster
        self.assertEqual(tid, c.id)
        self.assertEqual(False, c.more_tickets)
        self.assertEqual(100, c.total_tickets)
        self.assertEqual(150, c.total_transactions)
    
    def test_real_cluster(self):
        ticket1 = Ticket.objects.create(summary='one', topic=self.topic, state='expenses filed', rating_percentage=100)
        tid1 = ticket1.id
        Expediture.objects.create(ticket_id=tid1, description='exp', amount=100)
        
        ticket2 = Ticket.objects.create(summary='two', topic=self.topic, state='expenses filed', rating_percentage=100)
        tid2 = ticket2.id
        Expediture.objects.create(ticket_id=tid2, description='exp', amount=200)
        
        tr1 = Transaction.objects.create(date=datetime.date(2011, 12, 24), amount=100, other=self.user, description='pay1')
        tr1.tickets.add(ticket1)
        tr1.tickets.add(ticket2)
        
        # check there is a correct cluster
        cid = min(tid1, tid2)
        self.assertEqual(cid, Ticket.objects.get(id=tid1).cluster.id)
        self.assertEqual(cid, Ticket.objects.get(id=tid2).cluster.id)
        c = Ticket.objects.get(id=tid1).cluster
        self.assertEqual(True, c.more_tickets)
        self.assertEqual(300, c.total_tickets)
        self.assertEqual(100, c.total_transactions)
        
        # check status
        self.assertEqual('partially_paid', Ticket.objects.get(id=tid1).payment_status)
        self.assertEqual('partially_paid', Ticket.objects.get(id=tid2).payment_status)
        self.assertEqual(True, self.topic.payment_summary()['fuzzy'])
        self.assertEqual({'unpaid':200, 'paid':100, 'overpaid':0}, Cluster.cluster_sums())
        
        # complete payment
        tr2 = Transaction.objects.create(date=datetime.date(2011, 12, 25), amount=200, other=self.user, description='pay2')
        tr2.tickets.add(ticket2)
        
        # check cluster
        self.assertEqual(cid, Ticket.objects.get(id=tid1).cluster.id)
        self.assertEqual(cid, Ticket.objects.get(id=tid2).cluster.id)
        self.assertEqual(cid, Transaction.objects.get(id=tr1.id).cluster.id)
        self.assertEqual(cid, Transaction.objects.get(id=tr2.id).cluster.id)
        c = Transaction.objects.get(id=tr2.id).cluster
        self.assertEqual(True, c.more_tickets)
        self.assertEqual(300, c.total_tickets)
        self.assertEqual(300, c.total_transactions)
        
        # check status
        self.assertEqual('paid', Ticket.objects.get(id=tid1).payment_status)
        self.assertEqual('paid', Ticket.objects.get(id=tid2).payment_status)
        self.assertEqual({'fuzzy':False, 'unpaid':0, 'paid':300, 'overpaid':0}, self.topic.payment_summary())
        self.assertEqual({'unpaid':0, 'paid':300, 'overpaid':0}, Cluster.cluster_sums())
        
        # overpay ticket1
        tr1p = Transaction.objects.create(date=datetime.date(2011, 12, 26), amount=5, other=self.user, description='pay1plus')
        tr1p.tickets.add(ticket1)
        
        self.assertEqual(cid, Transaction.objects.get(id=tr1p.id).cluster.id)
        self.assertEqual('overpaid', Ticket.objects.get(id=tid1).payment_status)
        self.assertEqual('overpaid', Ticket.objects.get(id=tid2).payment_status)
        self.assertEqual(True, self.topic.payment_summary()['fuzzy'])
        self.assertEqual({'unpaid':0, 'paid':300, 'overpaid':5}, Cluster.cluster_sums())
        
        # separate clusters
        tr1.tickets.remove(ticket2)
        
        self.assertEqual(tid1, Ticket.objects.get(id=tid1).cluster.id)
        self.assertEqual(tid1, Transaction.objects.get(id=tr1.id).cluster.id)
        self.assertEqual(tid1, Transaction.objects.get(id=tr1p.id).cluster.id)
        self.assertEqual(tid2, Ticket.objects.get(id=tid2).cluster.id)
        self.assertEqual(tid2, Transaction.objects.get(id=tr2.id).cluster.id)
        
        self.assertEqual(False, Ticket.objects.get(id=tid1).cluster.more_tickets)
        self.assertEqual('overpaid', Ticket.objects.get(id=tid1).payment_status)
        
        self.assertEqual(False, Ticket.objects.get(id=tid2).cluster.more_tickets)
        self.assertEqual('paid', Ticket.objects.get(id=tid2).payment_status)
        
        self.assertEqual({'fuzzy':False, 'unpaid':0, 'paid':300, 'overpaid':5}, self.topic.payment_summary())
        self.assertEqual({'unpaid':0, 'paid':300, 'overpaid':5}, Cluster.cluster_sums())
        
        # reconnect make ticket2 overpaid again
        tr1.tickets.add(ticket2)
        self.assertEqual('overpaid', Ticket.objects.get(id=tid2).payment_status)
        self.assertEqual(True, self.topic.payment_summary()['fuzzy'])
        self.assertEqual({'unpaid':0, 'paid':300, 'overpaid':5}, Cluster.cluster_sums())

    def test_cluster_transaction_delete(self):
        ticket = Ticket.objects.create(summary='one', topic=self.topic, state='expenses filed', rating_percentage=100)
        tid = ticket.id
        Expediture.objects.create(ticket_id=tid, description='exp', amount=100)
        
        tr1 = Transaction.objects.create(date=datetime.date(2011, 12, 24), amount=100, other=self.user, description='pay1')
        tr1.tickets.add(ticket)
        self.assertEqual('paid', Ticket.objects.get(id=tid).payment_status)
        self.assertEqual({'fuzzy':False, 'unpaid':0, 'paid':100, 'overpaid':0}, self.topic.payment_summary())
        self.assertEqual({'unpaid':0, 'paid':100, 'overpaid':0}, Cluster.cluster_sums())
        
        tr2 = Transaction.objects.create(date=datetime.date(2011, 12, 25), amount=5, other=self.user, description='pay1plus')
        tr2.tickets.add(ticket)
        self.assertEqual('overpaid', Ticket.objects.get(id=tid).payment_status)
        self.assertEqual({'fuzzy':False, 'unpaid':0, 'paid':100, 'overpaid':5}, self.topic.payment_summary())
        self.assertEqual({'unpaid':0, 'paid':100, 'overpaid':5}, Cluster.cluster_sums())
        
        # delete tr2 to make ticket 'paid' again
        tr2.delete()
        self.assertEqual('paid', Ticket.objects.get(id=tid).payment_status)
        self.assertEqual({'fuzzy':False, 'unpaid':0, 'paid':100, 'overpaid':0}, self.topic.payment_summary())
        self.assertEqual({'unpaid':0, 'paid':100, 'overpaid':0}, Cluster.cluster_sums())
    
    def test_cluster_ticket_delete(self):
        ticket1 = Ticket.objects.create(summary='one', topic=self.topic, state='expenses filed', rating_percentage=100)
        tid1 = ticket1.id
        Expediture.objects.create(ticket_id=tid1, description='exp', amount=100)
        
        # pay ticket with one transaction
        tr1 = Transaction.objects.create(date=datetime.date(2011, 12, 25), amount=100, other=self.user, description='pay1')
        tr1.tickets.add(ticket1)
        self.assertEqual('paid', Ticket.objects.get(id=tid1).payment_status)
        self.assertEqual({'fuzzy':False, 'unpaid':0, 'paid':100, 'overpaid':0}, self.topic.payment_summary())
        self.assertEqual({'unpaid':0, 'paid':100, 'overpaid':0}, Cluster.cluster_sums())
        
        # add another ticket to the transaction cluster
        ticket2 = Ticket.objects.create(summary='two', topic=self.topic, state='expenses filed', rating_percentage=100)
        tid2 = ticket2.id
        Expediture.objects.create(ticket_id=tid2, description='exp', amount=50)
        tr1.tickets.add(ticket2)
        self.assertEqual('partially_paid', Ticket.objects.get(id=tid1).payment_status)
        self.assertEqual('partially_paid', Ticket.objects.get(id=tid1).payment_status)
        self.assertEqual(True, self.topic.payment_summary()['fuzzy'])
        self.assertEqual({'unpaid':50, 'paid':100, 'overpaid':0}, Cluster.cluster_sums())
        
        # delete tr2 to make ticket 'paid' again
        ticket2.delete()
        self.assertEqual('paid', Ticket.objects.get(id=tid1).payment_status)
        self.assertEqual({'fuzzy':False, 'unpaid':0, 'paid':100, 'overpaid':0}, self.topic.payment_summary())
        self.assertEqual({'unpaid':0, 'paid':100, 'overpaid':0}, Cluster.cluster_sums())

class UserProfileTests(TestCase):
    def test_simple_create(self):
        user = User.objects.create(username='new_user')
        try:
            profile = user.get_profile()
        except (SiteProfileNotAvailable, UserProfile.DoesNotExist):
            self.assertTrue(False)

class DocumentAccessTests(TestCase):
    def setUp(self):
        self.owner = {'user': User.objects.create(username='ticket_owner'), 'password':'pw1'}
        self.other_user = {'user':User.objects.create(username='other_user'), 'password':'pwo'}
        for u in (self.owner, self.other_user):
            u['user'].set_password(u['password'])
            u['user'].save()
    
        self.topic = Topic.objects.create(name='test_topic', ticket_expenses=True, grant=Grant.objects.create(full_name='g', short_name='g'))
        self.ticket = Ticket.objects.create(summary='ticket', topic=self.topic, requested_user=self.owner['user'])
        
        self.doc = {'name':'test.txt', 'content_type':'text/plain', 'payload':'hello, world!'}
        document = Document(ticket=self.ticket, filename=self.doc['name'], size=len(self.doc['payload']), content_type=self.doc['content_type'])
        document.payload.save(self.doc['name'], ContentFile(self.doc['payload']))
    
    def check_user_access(self, user, can_see, can_edit):
        c = Client()
        if user != None:
            c.login(username=user['user'].username, password=user['password'])
            deny_code = 403
        else:
            deny_code = 302
        
        response = c.get(reverse('ticket_detail', kwargs={'pk':self.ticket.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user_can_see_documents'], can_see)
        self.assertEqual(response.context['user_can_edit_documents'], can_edit)
        
        response = c.get(reverse('edit_ticket_docs', kwargs={'pk':self.ticket.id}))
        self.assertEqual(response.status_code, {True:200, False:deny_code}[can_edit])
        
        response = c.get(reverse('upload_ticket_doc', kwargs={'pk':self.ticket.id}))
        self.assertEqual(response.status_code, {True:200, False:deny_code}[can_edit])
        
        response = c.get(reverse('download_document', kwargs={'ticket_id':self.ticket.id, 'filename':self.doc['name']}))
        if can_see:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, self.doc['payload'])
        else:
            self.assertEqual(response.status_code, deny_code)
        
    
    def test_anonymous_user_access(self):
        self.check_user_access(user=None, can_see=False, can_edit=False)
    
    def test_unrelated_user_access(self):
        self.check_user_access(user=self.other_user, can_see=False, can_edit=False)
    
    def test_ticket_owner_access(self):
        self.check_user_access(user=self.owner, can_see=True, can_edit=True)
    
    def test_auditor_access(self):
        topic_content = ContentType.objects.get(app_label='tracker', model='Document')
        ou = self.other_user['user']
        ou.user_permissions.add(Permission.objects.get(content_type=topic_content, codename='see_all_docs'))
        ou.save()
        self.check_user_access(user=self.other_user, can_see=True, can_edit=False)
    
    def test_supervisor_access(self):
        topic_content = ContentType.objects.get(app_label='tracker', model='Document')
        ou = self.other_user['user']
        ou.user_permissions.add(Permission.objects.get(content_type=topic_content, codename='edit_all_docs'))
        ou.save()
        self.check_user_access(user=self.other_user, can_see=True, can_edit=True)
