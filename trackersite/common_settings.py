# -*- coding: utf-8 -*-
from os.path import dirname, abspath, join
from django.utils.translation import ugettext_lazy as _

SITE_DIR = abspath(dirname(__file__))
PROJECT_DIR = abspath(join(dirname(__file__), '..'))
_IGNORE = ('_IGNORE', '__builtins__', '__doc__', '__file__', '__name__', '__package__', 'os')

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

TEMPLATE_DIRS = (
    join(SITE_DIR, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages",
    "tracker.context_processors.currency",
)

STATICFILES_DIRS = (
    join(PROJECT_DIR, 'static'),
)

LOCALE_PATHS = (
    join(SITE_DIR, 'locale'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'django.contrib.comments',
    'django.contrib.messages',
    'south',
    'tracker',
    'users',
    'customcomments',
    'sendfile',
)

COMMENTS_APP = 'customcomments'

ROOT_URLCONF = 'urls'
LOGIN_URL = '/account/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_URL = '/account/logout/'

MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.FallbackStorage'

TRACKER_CURRENCY = _('CZK')

LANGUAGES = (
    ('en', _('English')),
    ('cs', _('Czech')),
)
