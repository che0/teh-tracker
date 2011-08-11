# -*- coding: utf-8 -*-
from django.contrib import admin
from tracker import models

class MediaInfoAdmin(admin.TabularInline):
    model = models.MediaInfo

class ExpeditureAdmin(admin.TabularInline):
    model = models.Expediture

class TicketAdmin(admin.ModelAdmin):
    def queryset(self, request):
        qs = super(TicketAdmin, self).queryset(request)
        if request.user.has_perm('tracker.supervisor'):
            return qs
        else:
            return qs.extra(where=['topic_id in (select topic_id from tracker_topic_admin where user_id = %s)'], params=[request.user.id])
    
    exclude = ('updated', )
    list_display = ('summary', 'topic', 'requested_by', 'status')
    list_filter = ('topic', 'status')
    inlines = [MediaInfoAdmin, ExpeditureAdmin]
admin.site.register(models.Ticket, TicketAdmin)

class TopicAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        else:
            return ('admin', )
    
    def queryset(self, request):
        if request.user.has_perm('tracker.supervisor'):
            return super(TopicAdmin, self).queryset(request)
        else:
            return request.user.topic_set.all()
    
    list_display = ('name', 'open_for_tickets', 'detailed_tickets')
    filter_horizontal = ('admin', )
admin.site.register(models.Topic, TopicAdmin)
