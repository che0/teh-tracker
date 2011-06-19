# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url
from django.contrib.auth import views as auth

urlpatterns = patterns('',
    url(r'^login/$', auth.login, kwargs={'template_name':'users/login.html'}, name='login'),
    url(r'^logout/$', auth.logout, kwargs={'template_name':'users/logout.html'}, name='logout'),
    url(r'^register/$', 'users.views.register', name='register'),
)
