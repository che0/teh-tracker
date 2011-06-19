# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from django.views.generic import RedirectView
from django.contrib import admin
from django.contrib.auth import views as auth

import tracker.urls
import users.urls

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='old/'), name='index'),
    url(r'^old/', include(tracker.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^users/', include(users.urls)),
)
