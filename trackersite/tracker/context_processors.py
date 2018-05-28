# -*- coding: utf-8 -*-
from django.conf import settings

def currency(request):
	return {'CURRENCY': settings.TRACKER_CURRENCY}

def base_url(request):
	return {'BASE_URL': settings.BASE_URL}