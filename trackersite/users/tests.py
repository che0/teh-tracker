# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from django.contrib.auth.models import User

class CreateUserTest(TestCase):
    def test_user_registration(self):
        response = Client().post(reverse('register'), {'username':'fooUser', 'password1':'foo', 'password2':'foo'})
        self.assertEqual(302, response.status_code)
        
        user = User.objects.get(username='fooUser')
        self.assertTrue(user.check_password('foo'))

