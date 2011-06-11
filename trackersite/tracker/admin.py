# -*- coding: utf-8 -*-
from django.contrib import admin
from tracker.models import Ticket

class TicketAdmin(admin.ModelAdmin):
    exclude = ('updated', )
    list_display = ('summary', 'topic', 'requested_by', 'status')
admin.site.register(Ticket, TicketAdmin)
