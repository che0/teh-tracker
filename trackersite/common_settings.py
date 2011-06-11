# -*- coding: utf-8 -*-
from os.path import dirname, abspath, join
PROJECT_DIR = abspath(join(dirname(__file__), '..'))

COMMON_TEMPLATE_DIRS = (
    join(PROJECT_DIR, 'templates'),
)

COMMON_STATICFILES_DIRS = (
    join(PROJECT_DIR, 'static'),
)    

COMMON_INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'south',
    'tracker',
)

ROOT_URLCONF = 'urls'
