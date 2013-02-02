# -*- coding: utf-8 -*-
from django import template
from django.utils.safestring import mark_safe
from django.conf import settings
from django.utils.formats import number_format

register = template.Library()

@register.filter
def money(value):
    if value == 0:
        out = '0'
    else:
        out = number_format(value, 2)
    return mark_safe(u'%s&nbsp;%s' % (out, settings.TRACKER_CURRENCY))
