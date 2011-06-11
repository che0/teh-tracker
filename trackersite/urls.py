# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from django.views.generic import RedirectView
from django.contrib import admin

import tracker.urls

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='old/')),
    url(r'^old/', include(tracker.urls)),
    url(r'^admin/', include(admin.site.urls)),
)
