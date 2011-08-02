# -*- coding: utf-8 -*-
from django.contrib import admin
from tracker import models

class MediaInfoAdmin(admin.TabularInline):
    model = models.MediaInfo

class ExpeditureAdmin(admin.TabularInline):
    model = models.Expediture

class TicketAdmin(admin.ModelAdmin):
    exclude = ('updated', )
    list_display = ('summary', 'topic', 'requested_by', 'status')
    list_filter = ('topic', 'status')
    inlines = [MediaInfoAdmin, ExpeditureAdmin]
admin.site.register(models.Ticket, TicketAdmin)

class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'open_for_tickets', 'detailed_tickets')
admin.site.register(models.Topic, TopicAdmin)
