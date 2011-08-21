# -*- coding: utf-8 -*-
import datetime

from django.db.models import Q
from django.forms import ModelForm, ModelChoiceField, ValidationError, Media, TextInput, Textarea
from django.forms.models import inlineformset_factory
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseBadRequest
from django.utils.functional import curry, lazy
from django.utils.translation import ugettext as _
from django.views.generic import DetailView
from django.contrib.admin import widgets as adminwidgets
from django.conf import settings
from django.utils import simplejson as json
from django.core.urlresolvers import reverse

from tracker.models import Ticket, Topic, MediaInfo

class TicketDetailView(DetailView):
    model = Ticket
    
    def get_context_data(self, **kwargs):
        context = super(TicketDetailView, self).get_context_data(**kwargs)
        context['user_can_edit_ticket'] = context['ticket'].can_edit(self.request.user)
        return context
ticket_detail = TicketDetailView.as_view()

def topics_js(request):
    data = {}
    for t in Topic.objects.all():
        data[t.id] = {}
        for attr in ('form_description', 'ticket_media', 'ticket_expenses'):
            data[t.id][attr] = getattr(t, attr)
    
    content = 'topics_table = %s;' % json.dumps(data)
    return HttpResponse(content, content_type='text/javascript')

class TicketForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(TicketForm, self).__init__(*args, **kwargs)
        self.fields['topic'].queryset = self.get_topic_queryset()
    
    def get_topic_queryset(self):
        return Topic.objects.filter(open_for_tickets=True)
    
    def _media(self):
        return super(TicketForm, self).media + Media(js=('ticketform.js', reverse('topics_js')))
    media = property(_media)
    
    class Meta:
        model = Ticket
        exclude = ('created', 'updated', 'requested_by', 'state', 'custom_state', 'rating_percentage', 'amount_paid')
        widgets = {
            'event_date': adminwidgets.AdminDateWidget(),
            'summary': TextInput(attrs={'size':'40'}),
            'description': Textarea(attrs={'rows':'4', 'cols':'60'}),
        }

def get_edit_ticket_form_class(ticket):
    class EditTicketForm(TicketForm):
        def get_topic_queryset(self):
            return Topic.objects.filter(Q(open_for_tickets=True) | Q(id=ticket.topic.id))
    
    return EditTicketForm

adminCore = Media(js=(
    settings.ADMIN_MEDIA_PREFIX + "js/jquery.min.js",
    settings.STATIC_URL + "jquery.both.js",
    settings.ADMIN_MEDIA_PREFIX + "js/core.js",
    settings.ADMIN_MEDIA_PREFIX + "js/inlines.js",
))

MEDIAINFO_FIELDS = ('url', 'description', 'count')
def mediainfo_formfield(f, **kwargs):
    if f.name == 'url':
        kwargs['widget'] = TextInput(attrs={'size':'60'})
    elif f.name == 'count':
        kwargs['widget'] = TextInput(attrs={'size':'4'})
    return f.formfield(**kwargs)
mediainfoformset_factory = curry(inlineformset_factory, Ticket, MediaInfo, fields=MEDIAINFO_FIELDS, formfield_callback=mediainfo_formfield)

@login_required
def create_ticket(request):
    MediaInfoFormSet = mediainfoformset_factory(extra=2, can_delete=False)
    
    if request.method == 'POST':
        ticketform = TicketForm(request.POST)
        try:
            mediainfo = MediaInfoFormSet(request.POST, prefix='mediainfo')
        except ValidationError, e:
            return HttpResponseBadRequest(unicode(e))
        
        if ticketform.is_valid() and mediainfo.is_valid():
            ticket = ticketform.save(commit=False)
            ticket.requested_by = request.user.username
            ticket.state = 'for consideration'
            ticket.save()
            ticketform.save_m2m()
            if ticket.topic.ticket_media:
                mediainfo.instance = ticket
                mediainfo.save()
            
            messages.success(request, _('Ticket %s created.') % ticket)
            return HttpResponseRedirect(ticket.get_absolute_url())
    else:
        initial = {'event_date': datetime.date.today()}
        if 'topic' in request.GET:
            initial['topic'] = request.GET['topic']
        ticketform = TicketForm(initial=initial)
        mediainfo = MediaInfoFormSet(prefix='mediainfo')
    
    return render(request, 'tracker/create_ticket.html', {
        'ticketform': ticketform,
        'mediainfo': mediainfo,
        'form_media': adminCore + ticketform.media + mediainfo.media,
    })

@login_required
def edit_ticket(request, pk):
    ticket = get_object_or_404(Ticket, id=pk)
    if not ticket.can_edit(request.user):
        return HttpResponseForbidden(_('You cannot edit this ticket.'))
    TicketEditForm = get_edit_ticket_form_class(ticket)
    
    MediaInfoFormSet = mediainfoformset_factory(extra=1, can_delete=True)
    
    if request.method == 'POST':
        ticketform = TicketEditForm(request.POST, instance=ticket)
        try:
            mediainfo = MediaInfoFormSet(request.POST, prefix='mediainfo', instance=ticket)
        except ValidationError, e:
            return HttpResponseBadRequest(unicode(e))
        
        if ticketform.is_valid() and mediainfo.is_valid():
            ticket = ticketform.save()
            mediainfo.save()
                
            messages.success(request, _('Ticket %s saved.') % ticket)
            return HttpResponseRedirect(ticket.get_absolute_url())
    else:
        ticketform = TicketEditForm(instance=ticket)
        mediainfo = MediaInfoFormSet(prefix='mediainfo', instance=ticket)
    
    return render(request, 'tracker/edit_ticket.html', {
        'ticket': ticket,
        'ticketform': ticketform,
        'mediainfo': mediainfo,
        'form_media': adminCore + ticketform.media + mediainfo.media,
    })
