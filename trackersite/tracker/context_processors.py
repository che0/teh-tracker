# -*- coding: utf-8 -*-
from django.conf import settings

def currency(request):
	return {'CURRENCY': settings.TRACKER_CURRENCY}
