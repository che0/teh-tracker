# -*- coding: utf-8 -*-
# Django project settings for Travis-CI
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'tracker',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'tracker-test-cache',
    }
}

SECRET_KEY='42'
TRACKER_DOCS_ROOT = os.path.join(os.environ['DEPLOY_DIR'], 'docs')
SITE_ID = 1
ADMIN_MEDIA_PREFIX = '/static/admin/'
STATIC_URL = '/static/'
RECAPTCHA_PUBLIC_KEY = ''
RECAPTCHA_PRIVATE_KEY = ''
SENDFILE_BACKEND = 'sendfile.backends.development'

import common_settings as _common
for item in dir(_common):
    if item not in _common._IGNORE:
        locals()[item] = getattr(_common, item)
