# -*- coding: utf-8 -*-
from django.contrib import admin
from tracker import models

class TicketAdmin(admin.ModelAdmin):
    exclude = ('updated', )
    list_display = ('summary', 'topic', 'requested_by', 'status')
admin.site.register(models.Ticket, TicketAdmin)

class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'open_for_tickets')
admin.site.register(models.Topic, TopicAdmin)
