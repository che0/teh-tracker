# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from django.views.generic import RedirectView
from django.contrib import admin
from django.contrib.auth import views as auth

import tracker.urls
import users.urls

admin.autodiscover()

js_info_dict = {
    'packages': ('django.contrib.admin'),
    # local site stuff should be covered by LOCALE_PATHS common setting
}

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='tickets/', permanent=False), name='index'),
    url(r'', include(tracker.urls)), # tracker urls are included directly in web root
    url(r'^admin/', include(admin.site.urls)),
    url(r'^users/', include(users.urls)),
    url(r'^js/i18n\.js$', 'django.views.i18n.javascript_catalog', js_info_dict),
)
