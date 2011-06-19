# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from django.contrib.auth.models import User

class CreateUserTest(TestCase):
    def test_user_registration(self):
        USERNAME, PW = 'foouser', 'foo'
        response = Client().post(reverse('register'), {'username':USERNAME, 'password1':PW, 'password2':PW})
        self.assertEqual(302, response.status_code)
        
        # user exists
        user = User.objects.get(username=USERNAME)
        self.assertTrue(user.check_password(PW))
        
        # login works
        self.assertTrue(Client().login(username=USERNAME, password=PW))
