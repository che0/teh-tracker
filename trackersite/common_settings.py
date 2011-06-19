# -*- coding: utf-8 -*-
from os.path import dirname, abspath, join
PROJECT_DIR = abspath(join(dirname(__file__), '..'))

TEMPLATE_DIRS = (
    join(PROJECT_DIR, 'templates'),
)

STATICFILES_DIRS = (
    join(PROJECT_DIR, 'static'),
)    

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'django.contrib.comments',
    'south',
    'tracker',
)

ROOT_URLCONF = 'urls'
