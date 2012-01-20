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
    
    exclude = ('updated', 'sort_date', 'cluster')
    list_display = ('sort_date', 'id', 'summary', 'topic', 'requested_by', 'state_str')
    list_display_links = ('summary',)
    list_filter = ('topic', 'state')
    date_hierarchy = 'sort_date'
    search_fields = ['id', 'requested_user__username', 'requested_text', 'summary']
    inlines = [MediaInfoAdmin, ExpeditureAdmin]
admin.site.register(models.Ticket, TicketAdmin)

class TopicAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if request.user.has_perm('tracker.supervisor'):
            return ()
        else:
            return ('admin', )
    
    def queryset(self, request):
        if request.user.has_perm('tracker.supervisor'):
            return super(TopicAdmin, self).queryset(request)
        else:
            return request.user.topic_set.all()
    
    list_display = ('name', 'open_for_tickets', 'ticket_media', 'ticket_expenses')
    filter_horizontal = ('admin', )
admin.site.register(models.Topic, TopicAdmin)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'other', 'amount', 'description', 'ticket_ids', 'accounting_info')
    list_display_links = ('amount', 'description')
    filter_vertical = ('tickets', )
    exclude = ('cluster', )
admin.site.register(models.Transaction, TransactionAdmin)
