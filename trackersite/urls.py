# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from django.http import HttpResponse
from django.views.generic import RedirectView, TemplateView
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
    url(r'^account/', include(users.urls)),
    url(r'^lang/$', TemplateView.as_view(template_name='choose_language.html'), name='choose_language'),
    url(r'^lang/set/$', 'django.views.i18n.set_language', name='set_language'),
    url(r'^js/i18n\.js$', 'django.views.i18n.javascript_catalog', js_info_dict),
    url(r'^robots\.txt$', lambda x: HttpResponse("User-agent: *\nDisallow: /\n", mimetype="text/plain")),
)
