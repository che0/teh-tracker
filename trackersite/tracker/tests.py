# -*- coding: utf-8 -*-

import datetime
import re
from decimal import Decimal

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.conf import settings
import StringIO
import csv

from users.models import UserWrapper
from tracker.models import Ticket, Topic, FinanceStatus, Grant, MediaInfo, Expediture, TrackerProfile, Document, Cluster

class SimpleTicketTest(TestCase):
    def setUp(self):
        self.topic = Topic(name='topic1', grant=Grant.objects.create(full_name='g', short_name='g', slug='g'))
        self.topic.save()

        self.ticket1 = Ticket(summary='foo', requested_text='req1', topic=self.topic, description='foo foo')
        self.ticket1.save()

        self.ticket2 = Ticket(summary='bar', requested_text='req2', topic=self.topic, description='bar bar')
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

    def _test_one_feed(self, url_name, topic_id, expected_ticket_count):
        url_kwargs = {'pk':topic_id} if topic_id is not None else {}
        response = Client().get(reverse(url_name, kwargs=url_kwargs))
        self.assertEqual(response.status_code, 200)
        items_in_response = re.findall(r'<item>', response.content) # ugly, mostly works
        self.assertEqual(expected_ticket_count, len(items_in_response))

    def test_feeds(self):
        self.ticket1.add_acks('user_content')
        self._test_one_feed('ticket_list_feed', None, 2)
        self._test_one_feed('ticket_submitted_feed', None, 1)
        self._test_one_feed('topic_ticket_feed', self.topic.id, 2)
        self._test_one_feed('topic_submitted_ticket_feed', self.topic.id, 1)

    def test_historical(self):
        self.ticket1.imported = True
        self.ticket1.save()
        self.assertEqual(self.ticket1.state_str(), 'historical')

class OldRedirectTests(TestCase):
    def setUp(self):
        self.topic = Topic(name='topic', grant=Grant.objects.create(full_name='g', short_name='g', slug='g'))
        self.topic.save()
        self.ticket = Ticket(summary='foo', requested_text='req', topic=self.topic, description='foo foo')
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
        self.topic = Topic(name='topic', grant=Grant.objects.create(full_name='g', short_name='g', slug='g'))
        self.topic.save()

    def test_empty_ticket(self):
        empty_ticket = Ticket(topic=self.topic, requested_text='someone', summary='empty ticket')
        empty_ticket.save()

        self.assertEqual(0, empty_ticket.media_count()['objects'])
        self.assertEqual(0, empty_ticket.expeditures()['count'])
        self.assertEqual(0, self.topic.media_count()['objects'])
        self.assertEqual(0, self.topic.expeditures()['count'])

    def test_full_ticket(self):
        full_ticket = Ticket(topic=self.topic, requested_text='someone', summary='full ticket')
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
        self.open_topic = Topic(name='test_topic', open_for_tickets=True, ticket_media=True, grant=Grant.objects.create(full_name='g', short_name='g', slug='g'))
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
                'preexpediture-INITIAL_FORMS': '0',
                'preexpediture-TOTAL_FORMS': '0',
            })
        self.assertEqual(200, response.status_code)
        self.assertFormError(response, 'ticketform', 'summary', 'This field is required.')
        self.assertFormError(response, 'ticketform', 'deposit', 'This field is required.')

        response = c.post(reverse('create_ticket'), {
                'summary': 'ticket',
                'topic': self.open_topic.id,
                'description': 'some desc',
                'deposit': '0',
                'mediainfo-INITIAL_FORMS': '0',
                'mediainfo-TOTAL_FORMS': '0',
                'expediture-INITIAL_FORMS': '0',
                'expediture-TOTAL_FORMS': '0',
                'preexpediture-INITIAL_FORMS': '0',
                'preexpediture-TOTAL_FORMS': '0',
            })
        self.assertEqual(302, response.status_code)
        self.assertEqual(1, Ticket.objects.count())
        ticket = Ticket.objects.order_by('-created')[0]
        self.assertEqual(self.user, ticket.requested_user)
        self.assertEqual(self.user.username, ticket.requested_by())
        self.assertEqual('draft', ticket.state_str())
        self.assertRedirects(response, reverse('ticket_detail', kwargs={'pk':ticket.id}))

    def test_ticket_creation_with_media(self):
        c = self.get_client()
        response = c.post(reverse('create_ticket'), {
                'summary': 'ticket',
                'topic': self.open_topic.id,
                'description': 'some desc',
                'deposit': '0',
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
                'preexpediture-INITIAL_FORMS': '0',
                'preexpediture-TOTAL_FORMS': '0',
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
                'deposit': '0',
                'mediainfo-INITIAL_FORMS': '0',
                'mediainfo-TOTAL_FORMS': '0',
                'expediture-INITIAL_FORMS': '0',
                'expediture-TOTAL_FORMS': '0',
                'preexpediture-INITIAL_FORMS': '0',
                'preexpediture-TOTAL_FORMS': '0',
            })
        self.assertEqual(200, response.status_code)
        self.assertFormError(response, 'ticketform', 'topic', 'Select a valid choice. That choice is not one of the available choices.')

    def test_closed_topic(self):
        closed_topic = Topic(name='closed topic', open_for_tickets=False, grant=Grant.objects.create(full_name='g', short_name='g', slug='g'))
        closed_topic.save()

        c = self.get_client()
        response = c.post(reverse('create_ticket'), {
                'summary': 'ticket',
                'topic': closed_topic.id,
                'description': 'some desc',
                'deposit': '0',
                'mediainfo-INITIAL_FORMS': '0',
                'mediainfo-TOTAL_FORMS': '0',
                'expediture-INITIAL_FORMS': '0',
                'expediture-TOTAL_FORMS': '0',
                'preexpediture-INITIAL_FORMS': '0',
                'preexpediture-TOTAL_FORMS': '0',
            })
        self.assertEqual(200, response.status_code)
        self.assertFormError(response, 'ticketform', 'topic', 'Select a valid choice. That choice is not one of the available choices.')

    def test_too_big_deposit(self):
        c = self.get_client()
        response = c.post(reverse('create_ticket'), {
                'summary': 'ticket',
                'topic': self.open_topic.id,
                'description': 'some desc',
                'deposit': '100',
                'mediainfo-INITIAL_FORMS': '0',
                'mediainfo-TOTAL_FORMS': '0',
                'expediture-INITIAL_FORMS': '0',
                'expediture-TOTAL_FORMS': '0',
                'preexpediture-INITIAL_FORMS': '0',
                'preexpediture-TOTAL_FORMS': '0',
            })
        self.assertEqual(200, response.status_code)
        self.assertFormError(response, 'ticketform', 'deposit', 'Your deposit is bigger than your preexpeditures')

    def test_too_big_deposit2(self):
        c = self.get_client()
        response = c.post(reverse('create_ticket'), {
                'summary': 'ticket',
                'topic': self.open_topic.id,
                'description': 'some desc',
                'deposit': '50.01',
                'mediainfo-INITIAL_FORMS': '0',
                'mediainfo-TOTAL_FORMS': '0',
                'expediture-INITIAL_FORMS': '0',
                'expediture-TOTAL_FORMS': '0',
                'preexpediture-INITIAL_FORMS': '0',
                'preexpediture-TOTAL_FORMS': '1',
                'preexpediture-0-description': 'foo',
                'preexpediture-0-amount': '50',
            })
        self.assertEqual(200, response.status_code)
        self.assertFormError(response, 'ticketform', 'deposit', 'Your deposit is bigger than your preexpeditures')

    def test_correct_deposit(self):
        c = self.get_client()
        response = c.post(reverse('create_ticket'), {
                'summary': 'ticket',
                'topic': self.open_topic.id,
                'description': 'some desc',
                'deposit': '30.1',
                'mediainfo-INITIAL_FORMS': '0',
                'mediainfo-TOTAL_FORMS': '0',
                'expediture-INITIAL_FORMS': '0',
                'expediture-TOTAL_FORMS': '0',
                'preexpediture-INITIAL_FORMS': '0',
                'preexpediture-TOTAL_FORMS': '2',
                'preexpediture-0-description': 'pre1',
                'preexpediture-0-amount': '10.0',
                'preexpediture-1-description': 'pre2',
                'preexpediture-1-amount': '20.1',
                'preexpediture-1-wage': 'true',
            })
        self.assertEqual(302, response.status_code)
        self.assertEqual(1, Ticket.objects.count())
        ticket = Ticket.objects.order_by('-created')[0]
        self.assertEqual(Decimal('30.1'), ticket.deposit)

        preexpeditures = ticket.preexpediture_set.order_by('description')
        self.assertEqual(2, len(preexpeditures))
        self.assertEqual('pre1', preexpeditures[0].description)
        self.assertEqual(Decimal(10), preexpeditures[0].amount)
        self.assertEqual(False, preexpeditures[0].wage)
        self.assertEqual('pre2', preexpeditures[1].description)
        self.assertEqual(Decimal('20.1'), preexpeditures[1].amount)
        self.assertEqual(True, preexpeditures[1].wage)

class TicketEditTests(TestCase):
    def test_correct_choices(self):
        grant = Grant.objects.create(full_name='g', short_name='g', slug='g')
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
        topic = Topic(name='topic', grant=Grant.objects.create(full_name='g', short_name='g', slug='g'))
        topic.save()

        password = 'my_password'
        user = User(username='my_user')
        user.set_password(password)
        user.save()

        ticket = Ticket(summary='ticket', topic=topic, requested_user=None, requested_text='foo')
        ticket.save()
        ticket.add_acks('close')

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

        ticket.ticketack_set.filter(ack_type='close').delete()
        response = c.get(reverse('edit_ticket', kwargs={'pk':ticket.id}))
        self.assertEqual(200, response.status_code) # now it should pass

        # try to submit the form
        response = c.post(reverse('edit_ticket', kwargs={'pk':ticket.id}), {
                'summary': 'new summary',
                'topic': ticket.topic.id,
                'description': 'new desc',
                'deposit': '0',
                'mediainfo-INITIAL_FORMS': '0',
                'mediainfo-TOTAL_FORMS': '0',
                'expediture-INITIAL_FORMS': '0',
                'expediture-TOTAL_FORMS': '0',
                'preexpediture-INITIAL_FORMS': '0',
                'preexpediture-TOTAL_FORMS': '0',
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
                'deposit': '0',
                'mediainfo-INITIAL_FORMS': '0',
                'mediainfo-TOTAL_FORMS': '1',
                'mediainfo-0-count': 'foo',
                'mediainfo-0-description': 'image 1',
                'mediainfo-0-url': 'http://www.example.com/image1.jpg',
                'expediture-INITIAL_FORMS': '0',
                'expediture-TOTAL_FORMS': '0',
                'preexpediture-INITIAL_FORMS': '0',
                'preexpediture-TOTAL_FORMS': '0',
            })
        self.assertEqual(200, response.status_code)
        self.assertEqual('Enter a whole number.', response.context['mediainfo'].forms[0].errors['count'][0])

        # b0rked expediture items aborts the submit
        response = c.post(reverse('edit_ticket', kwargs={'pk':ticket.id}), {
                'summary': 'ticket',
                'topic': ticket.topic.id,
                'description': 'some desc',
                'deposit': '0',
                'mediainfo-INITIAL_FORMS': '0',
                'mediainfo-TOTAL_FORMS': '0',
                'expediture-INITIAL_FORMS': '0',
                'expediture-TOTAL_FORMS': '1',
                'expediture-0-description': 'foo',
                'expediture-0-amount': '',
                'preexpediture-INITIAL_FORMS': '0',
                'preexpediture-TOTAL_FORMS': '0',
            })
        self.assertEqual(200, response.status_code)
        self.assertEqual('This field is required.', response.context['expeditures'].forms[0].errors['amount'][0])

        # add some inline items
        response = c.post(reverse('edit_ticket', kwargs={'pk':ticket.id}), {
                'summary': 'new summary',
                'topic': ticket.topic.id,
                'description': 'new desc',
                'deposit': '0',
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
                'preexpediture-INITIAL_FORMS': '0',
                'preexpediture-TOTAL_FORMS': '0',
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
                'deposit': '0',
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
                'preexpediture-INITIAL_FORMS': '0',
                'preexpediture-TOTAL_FORMS': '0',
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

        # add preexpeditures, and amount flag preack
        deposit_amount = Decimal('12324.37')
        ticket = Ticket.objects.get(id=ticket.id)
        ticket.deposit = deposit_amount
        ticket.preexpediture_set.create(description='some preexp', amount=15)
        ticket.save()
        ticket.add_acks('precontent')

        # edit should work and ignore new data
        response = c.post(reverse('edit_ticket', kwargs={'pk':ticket.id}), {
            'summary': 'new summary',
            'topic': ticket.topic.id,
            'description': 'new desc',
            'deposit': '333',
            'mediainfo-INITIAL_FORMS': '0',
            'mediainfo-TOTAL_FORMS': '0',
            'expediture-INITIAL_FORMS': '0',
            'expediture-TOTAL_FORMS': '0',
            'preexpediture-INITIAL_FORMS': '0',
            'preexpediture-TOTAL_FORMS': '0',
        })
        self.assertRedirects(response, reverse('ticket_detail', kwargs={'pk':ticket.id}))
        ticket = Ticket.objects.get(id=ticket.id)
        self.assertEqual(deposit_amount, ticket.deposit)
        self.assertEqual(1, ticket.preexpediture_set.count())

        # also, edit should work and not fail on missing preack-ignored fields
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
        ticket = Ticket.objects.get(id=ticket.id)
        self.assertEqual(deposit_amount, ticket.deposit)
        self.assertEqual(1, ticket.preexpediture_set.count())


class TicketAckTests(TestCase):
    def setUp(self):
        self.grant = Grant.objects.create(full_name='g', short_name='g', slug='g')
        self.topic = Topic.objects.create(name='t', grant=self.grant)
        self.password = 'my_password'
        self.user = User(username='my_user')
        self.user.set_password(self.password)
        self.user.save()
        self.ticket = Ticket.objects.create(summary='ticket', topic=self.topic, requested_user=self.user)

    def test_ack_user_edit(self):
        # two user acks are possible
        self.assertEqual(
            {'user_precontent', 'user_content', 'user_docs'},
            {a.ack_type for a in self.ticket.possible_user_acks()}
        )

        # add some acks, now only user_content is possible to add
        self.ticket.add_acks('user_docs', 'user_precontent')
        self.assertEqual(
            {'user_content',},
            {a.ack_type for a in self.ticket.possible_user_acks()}
        )

        # user_docs can be removed
        ud = self.ticket.ticketack_set.get(ack_type='user_docs')
        self.assertTrue(ud.user_removable)

        # content can't be removed
        self.ticket.add_acks('content')
        cont = self.ticket.ticketack_set.get(ack_type='content')
        self.assertFalse(cont.user_removable)

    def test_ack_user_delete(self):
        self.ticket.add_acks('user_docs')
        ud = self.ticket.ticketack_set.get(ack_type='user_docs')

        c = Client()
        c.login(username=self.user.username, password=self.password)
        delete_url = reverse('ticket_ack_delete', kwargs={'pk':self.ticket.id, 'ack_id':ud.id})
        response = c.get(delete_url)
        self.assertEqual(response.status_code, 200)

        response = c.post(delete_url)
        self.assertRedirects(response, reverse('ticket_detail', kwargs={'pk':self.ticket.id}))
        self.assertTrue('user_docs' not in self.ticket.ack_set())

    def test_ack_not_deletable_by_anon(self):
        self.ticket.add_acks('user_docs')
        ud = self.ticket.ticketack_set.get(ack_type='user_docs')

        c = Client()
        response = c.post(reverse('ticket_ack_delete', kwargs={'pk':self.ticket.id, 'ack_id':ud.id}))
        self.assertEqual(response.status_code, 403)

    def test_ack_not_deletable_when_admin_only(self):
        self.ticket.add_acks('content')
        cont = self.ticket.ticketack_set.get(ack_type='content')

        c = Client()
        c.login(username=self.user.username, password=self.password)
        response = c.post(reverse('ticket_ack_delete', kwargs={'pk':self.ticket.id, 'ack_id':cont.id}))
        self.assertEqual(response.status_code, 403)

    def test_topic_content_acks_per_user(self):
        c = Client()
        response = c.get(reverse('topic_content_acks_per_user'))
        self.assertEqual(response.status_code, 200)

    def test_topic_content_acks_per_user_csv(self):
        c = Client()
        response = c.get(reverse('topic_content_acks_per_user_csv'))
        self.assertEqual(response.status_code, 200)

class TicketEditLinkTests(TestCase):
    def setUp(self):
        self.topic = Topic(name='topic', grant=Grant.objects.create(full_name='g', short_name='g', slug='g'))
        self.topic.save()

        self.password = 'my_password'
        self.user = User(username='my_user')
        self.user.set_password(self.password)
        self.user.save()

        self.ticket = Ticket(summary='ticket', topic=self.topic, requested_user=None, requested_text='foo')
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
        self.topic = Topic(name='test_topic', open_for_tickets=True, ticket_media=True, grant=Grant.objects.create(full_name='g', short_name='g', slug='g'))
        self.topic.save()

        self.user = User(username='user')
        self.user.save()

        self.ticket = Ticket(summary='foo', requested_user=self.user, topic=self.topic, description='foo foo')
        self.ticket.save()

    def test_user_details(self):
        c = Client()
        response = c.get(UserWrapper(self.user).get_absolute_url())
        self.assertEqual(200, response.status_code)
        self.assertEqual(self.ticket, response.context['ticket_list'][0])

class SummaryTest(TestCase):
    def setUp(self):
        self.user = User(username='user')
        self.user.save()

        self.topic = Topic(name='test_topic', ticket_expenses=True, grant=Grant.objects.create(full_name='g', short_name='g', slug='g'))
        self.topic.save()

        self.ticket = Ticket(summary='foo', requested_user=self.user, topic=self.topic, rating_percentage=50)
        self.ticket.save()
        self.ticket.add_acks('content', 'docs', 'archive')
        self.ticket.expediture_set.create(description='foo', amount=200)
        self.ticket.expediture_set.create(description='foo', amount=100)
        self.ticket.mediainfo_set.create(description='foo', count=5)

        self.ticket2 = Ticket(summary='foo', requested_user=self.user, topic=self.topic, rating_percentage=100)
        self.ticket2.save()
        self.ticket2.add_acks('content', 'docs', 'archive')
        self.ticket2.expediture_set.create(description='foo', amount=600)
        self.ticket2.expediture_set.create(description='foo', amount=10)
        self.ticket2.mediainfo_set.create(description='foo', count=5)
        self.ticket2.mediainfo_set.create(description='foo', count=3)

    def test_topic_ticket_counts(self):
        self.assertEqual({'unpaid':2}, self.topic.tickets_per_payment_status())
        for e in self.ticket.expediture_set.all():
			e.paid = True
			e.save()
        self.assertEqual({'unpaid':1, 'paid':1}, self.topic.tickets_per_payment_status())

    def test_ticket_summary(self):
        self.ticket.ticketack_set.filter(ack_type='archive').delete()
        self.ticket.rating_percentage = None
        self.ticket.save()

        self.assertEqual({'objects':1, 'media':5}, self.ticket.media_count())
        self.assertEqual({'count':2, 'amount':300}, self.ticket.expeditures())
        self.assertEqual(0, self.ticket.accepted_expeditures())

        self.ticket.rating_percentage = 50
        self.ticket.save()
        self.assertEqual(0, self.ticket.accepted_expeditures())

        self.ticket.add_acks('archive')
        self.assertEqual(150, self.ticket.accepted_expeditures())

    def test_topic_summary(self):
        self.assertEqual({'objects':3, 'media':13}, self.topic.media_count())
        self.assertEqual({'count':4, 'amount':910}, self.topic.expeditures())
        self.assertEqual(150 + 610, self.topic.accepted_expeditures())

    def test_user_summary(self):
        profile = self.user.trackerprofile
        self.assertEqual({'objects':3, 'media':13}, profile.media_count())
        self.assertEqual(150 + 610, profile.accepted_expeditures())

    def test_topic_finance(self):
        response = Client().get(reverse('topic_finance'))
        self.assertEqual(response.status_code, 200)

class UserProfileTests(TestCase):
    def test_simple_create(self):
        user = User.objects.create(username='new_user')
        try:
            profile = user.trackerprofile
        except TrackerProfile.DoesNotExist:
            self.assertTrue(False)

class ImportTests(TestCase):

    def get_test_data(self, type):
        csvfile = StringIO.StringIO()
        csvwriter = csv.writer(csvfile, delimiter=';')
        if type == 'ticket':
            csvwriter.writerow(['event_date', 'summary', 'topic', 'event_url', 'description', 'deposit'])
            csvwriter.writerow([u'2010-04-23', u'Nazev ticketu', u'Nazev tematu', u'http://wikimedia.cz', u'Popis ticketu', u'0'])
        elif type == 'topic':
            csvwriter.writerow(['name', 'grant', 'new_tickets', 'media', 'preexpenses', 'expenses', 'description', 'form_description'])
            csvwriter.writerow([u'Nazev tematu', u'Nazev grantu', u'True', u'True', u'True', u'True', u'Popis tematu', u'Popis formulare tematu'])
        elif type == 'grant':
            csvwriter.writerow(['full_name', 'short_name', 'slug', 'description'])
            csvwriter.writerow([u'Nazev grantu', u'grant', u'grant', u'Popis'])
        elif type == 'user':
            csvwriter.writerow(['username', 'password', 'first_name', 'last_name', 'is_superuser', 'is_staff', 'is_active', 'email'])
            csvwriter.writerow([u'username', u'Heslo', u'name', u'surname', u'False', u'False', u'True', u'emailova@adresa.cz'])
        elif type == 'media':
            csvwriter.writerow(['ticket_id', 'url', 'description', 'number'])
            csvwriter.writerow(['1', 'http://wikimedia.cz', 'popis', '1'])
        elif type == 'expense':
            csvwriter.write(['ticket_id', 'description', 'amount', 'wage', 'accounting_info', 'paid'])
            csvwriter.write(['1', 'popisek', '100', True, 'accounting info', False])
        elif type == 'preexpense':
            csvwriter.write(['ticket_id', 'description', 'amount', 'wage'])
            csvwriter.write(['1', 'popisek', '100', True])
        csvfile.seek(0)
        return csvfile

    def reset_attempt(self, type):
        if type == 'ticket':
            for t in Ticket.objects.all():
                t.delete()
        if type == 'topic':
            for t in Topic.objects.all():
                t.delete()
        if type == 'grant':
            for t in Grant.objects.all():
                t.delete()
        if type == 'user':
            for t in User.objects.exclude(username='user').exclude(username='staffer').exclude(username='superuser'):
                t.delete()
        if type == 'media':
            for t in MediaInfo.objects.all():
                t.delete()
        if type == 'expense':
            for t in Expediture.objects.all():
                t.delete()
        if type == 'preexpense':
            for t in Preexpediture.objects.all():
                t.delete()


    def test_access_rights(self):
        user = {'user': User.objects.create(username='user'), 'password':'pw1'}
        staffer = {'user': User.objects.create(username='staffer', is_staff=True), 'password':'pw2'}
        superuser = {'user': User.objects.create(username='superuser', is_staff=True, is_superuser=True), 'password':'pw3'}
        for u in (user, staffer, superuser):
            u['user'].set_password(u['password'])
            u['user'].save()
        testConfigurations = [
            {
                'type': 'grant',
                'normal': 403,
                'staffer': 302,
                'superuser': 302,
            },
            {
                'type': 'topic',
                'normal': 403,
                'staffer': 302,
                'superuser': 302,
            },
            {
                'type': 'user',
                'normal': 403,
                'staffer': 403,
                'superuser': 302,
            },
            {
                'type': 'expense',
                'normal': 302,
                'staffer': 302,
                'superuser': 302
            },
            {
                'type': 'preexpense',
                'normal': 302,
                'staffer': 302,
                'superuser': 302
            },
        ]
        for testConfiguration in testConfigurations:
            c = Client()
            c.login(username=user['user'].username, password=user['password']) # Login with normal user account
            response = c.post(reverse('importcsv'), {
                'type': testConfiguration['type'],
                'csvfile': self.get_test_data(testConfiguration['type'])
            })
            self.assertEqual(testConfiguration['normal'], response.status_code)
            self.reset_attempt(testConfiguration['type'])
            c = Client()
            c.login(username=staffer['user'].username, password=staffer['password']) # Login with staffer user account
            response = c.post(reverse('importcsv'), {
                'type': testConfiguration['type'],
                'csvfile': self.get_test_data(testConfiguration['type'])
            })
            self.assertEqual(testConfiguration['staffer'], response.status_code)
            self.reset_attempt(testConfiguration['type'])
            c = Client()
            c.login(username=superuser['user'].username, password=superuser['password']) # Login with superuser user account
            response = c.post(reverse('importcsv'), {
                'type': testConfiguration['type'],
                'csvfile': self.get_test_data(testConfiguration['type'])
            })
            self.assertEqual(testConfiguration['superuser'], response.status_code)

class DocumentAccessTests(TestCase):
    def setUp(self):
        self.owner = {'user': User.objects.create(username='ticket_owner'), 'password':'pw1'}
        self.other_user = {'user':User.objects.create(username='other_user'), 'password':'pwo'}
        for u in (self.owner, self.other_user):
            u['user'].set_password(u['password'])
            u['user'].save()

        self.topic = Topic.objects.create(name='test_topic', ticket_expenses=True, grant=Grant.objects.create(full_name='g', short_name='g', slug='g'))
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
            self.assertEqual(''.join(response.streaming_content), self.doc['payload'])
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
