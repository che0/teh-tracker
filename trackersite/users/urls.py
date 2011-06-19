# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url
from django.contrib.auth import views as auth

from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView

urlpatterns = patterns('',
    url(r'^login/$', auth.login, kwargs={'template_name':'users/login.html'}, name='login'),
    url(r'^logout/$', auth.logout, kwargs={'template_name':'users/logout.html'}, name='logout'),
    url(r'^register/$', CreateView.as_view(
            form_class=UserCreationForm, template_name='users/register.html',
            success_url='/',
        ), name='register'),
)
