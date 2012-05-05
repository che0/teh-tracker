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
    readonly_fields = ('payment_status',)
    list_display = ('sort_date', 'id', 'summary', 'topic', 'requested_by', 'state_str', 'payment_status')
    list_display_links = ('summary',)
    list_filter = ('topic', 'state', 'payment_status')
    date_hierarchy = 'sort_date'
    search_fields = ['id', 'requested_user__username', 'requested_text', 'summary']
    inlines = [MediaInfoAdmin, ExpeditureAdmin]
admin.site.register(models.Ticket, TicketAdmin)

class TopicAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if request.user.has_perm('tracker.supervisor'):
            return ()
        else:
            return ('admin', 'grant')
    
    def queryset(self, request):
        if request.user.has_perm('tracker.supervisor'):
            return super(TopicAdmin, self).queryset(request)
        else:
            return request.user.topic_set.all()
    
    list_display = ('name', 'grant', 'open_for_tickets', 'ticket_media', 'ticket_expenses')
    list_filter = ('grant', )
    filter_horizontal = ('admin', )
admin.site.register(models.Topic, TopicAdmin)

class GrantAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('short_name',)}
admin.site.register(models.Grant, GrantAdmin)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'other_party', 'amount', 'description', 'ticket_ids', 'accounting_info')
    list_display_links = ('amount', 'description')
    filter_vertical = ('tickets', )
    exclude = ('cluster', )
admin.site.register(models.Transaction, TransactionAdmin)

# piggypatch admin site to display our own index template with some bonus links
admin.site.index_template = 'tracker/admin_index_override.html'
