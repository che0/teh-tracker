# -*- coding: utf-8 -*-
from django.core import mail
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from django.contrib.auth.models import User
from django.contrib.auth import views as auth_views

class CreateUserTest(TestCase):
    def test_user_registration(self):
        USERNAME, PW, EMAIL = 'foouser', 'foo', 'foo@example.com'
        response = Client().post(reverse('register'), {
            'username':USERNAME, 'password1':PW, 'password2':PW, 'email':EMAIL,
        })
        self.assertEqual(200, response.status_code)
        
        # user does not exist -> we've been killed by captcha
        self.assertEqual(0, len(User.objects.filter(username=USERNAME)))

class PasswordResetTests(TestCase):
    def test_password_reset(self):
        response = Client().get(reverse(auth_views.password_reset))
        self.assertEqual(200, response.status_code)
        
    def test_password_reset_requested(self):
        USERNAME, PW, EMAIL = 'foouser', 'foo', 'foo@example.com'
        u = User.objects.create(username=USERNAME, email=EMAIL)
        u.set_password(PW)
        u.save()
        
        response = Client().post(reverse(auth_views.password_reset), {
            'email': EMAIL,
        })
        self.assertRedirects(response, reverse(auth_views.password_reset_done))
        
        # sent an e-mail
        self.assertEqual(len(mail.outbox), 1)
    
    def test_password_reset_done(self):
        response = Client().get(reverse(auth_views.password_reset_done))
        self.assertEqual(200, response.status_code)

    def test_password_reset_confirm(self):
        response = Client().get(reverse(auth_views.password_reset_confirm, kwargs={
            'uidb64': 'a', 'token': 'a',
        }))
        self.assertEqual(200, response.status_code)

    def test_password_reset_complete(self):
        response = Client().get(reverse(auth_views.password_reset_complete))
        self.assertEqual(200, response.status_code)
