# -*- coding: utf-8 -*-
import datetime
import json
from collections import namedtuple

from django.db import models, connection
from django.db.models import Q
from django import forms
from django.forms.models import fields_for_model, inlineformset_factory, BaseInlineFormSet
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseBadRequest, Http404
from django.utils.functional import curry, lazy
from django.utils.translation import ugettext as _, ugettext_lazy
from django.views.generic import ListView, DetailView, FormView, DeleteView
from django.contrib.admin import widgets as adminwidgets
from django.conf import settings
from django.core.urlresolvers import reverse
from sendfile import sendfile

from tracker.models import Ticket, Topic, Grant, FinanceStatus, MediaInfo, Expediture, Preexpediture, Transaction, Cluster, TrackerProfile, Document, TicketAck, PossibleAck
from users.models import UserWrapper

class TicketListView(ListView):
    model = Ticket
    paginate_by = 50
    
    def get(self, request, *args, **kwargs):
        if kwargs.get('page', None) == '1':
            return HttpResponseRedirect(reverse('ticket_list'))
        else:
            return super(TicketListView, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        orderget = self.request.GET.get('order', 'sort_date')
        descasc = self.request.GET.get('descasc', 'desc')
        if descasc == 'asc':
            finalorder = orderget
        else:
            finalorder = '-' + orderget
        return super(TicketListView, self).get_queryset().select_related().order_by(finalorder)
ticket_list = TicketListView.as_view()

class CommentPostedCatcher(object):
    """ 
    View mixin that catches 'c' GET argument from comment framework
    and turns in into a success message.
    """
    def get(self, request, **kwargs):
        if 'c' in request.GET:
            messages.success(request, _('Comment posted, thank you.'))
            return HttpResponseRedirect(request.path)
        return super(CommentPostedCatcher, self).get(request, **kwargs)

class TicketDetailView(CommentPostedCatcher, DetailView):
    model = Ticket
    
    def get_context_data(self, **kwargs):
        user = self.request.user
        ticket = self.object
        context = super(TicketDetailView, self).get_context_data(**kwargs)
        context['user_can_edit_ticket'] = ticket.can_edit(user)
        admin_edit = user.is_staff and (user.has_perm('tracker.supervisor') or user.topic_set.filter(id=ticket.topic_id).exists())
        context['user_can_edit_ticket_in_admin'] = admin_edit
        context['user_can_edit_documents'] = ticket.can_edit_documents(user)
        context['user_can_see_documents'] = ticket.can_see_documents(user)
        return context
ticket_detail = TicketDetailView.as_view()

class TicketAckAddForm(forms.Form):
    comment = forms.CharField(required=False, max_length=255)

class TicketAckAddView(FormView):
    template_name = 'tracker/ticketack_add.html'
    form_class = TicketAckAddForm
    
    def get_form(self, form_class):
        ticket = get_object_or_404(Ticket, id=self.kwargs['pk'])
        if not (ticket.can_edit(self.request.user) and self.kwargs['ack_type'] in ticket.possible_user_ack_types()):
            raise Http404
        return form_class(**self.get_form_kwargs())
    
    def form_valid(self, form):
        ticket = get_object_or_404(Ticket, id=self.kwargs['pk'])
        ack = TicketAck.objects.create(
            ticket=ticket,
            ack_type=self.kwargs['ack_type'], 
            added_by=self.request.user,
            comment=form.cleaned_data['comment'],
        )
        msg = _('Ticket %(ticket_id)s confirmation "%(confirmation)s" has been added.') % {
            'ticket_id':ticket.id, 'confirmation':ack.get_ack_type_display(),
        }
        messages.success(self.request, msg)
        return HttpResponseRedirect(ticket.get_absolute_url())
    
    def get_context_data(self, **kwargs):
        kwargs.update({
            'ticket': get_object_or_404(Ticket, id=self.kwargs['pk']),
            'ticketack': PossibleAck(self.kwargs['ack_type']),
        })
        return kwargs
ticket_ack_add = TicketAckAddView.as_view()

class TicketAckDeleteView(DeleteView):
    model = TicketAck
    
    def get_object(self):
        try:
            self.ticket = Ticket.objects.get(id=self.kwargs['pk'])
            ack = self.ticket.ticketack_set.get(id=self.kwargs['ack_id'])
        except (Ticket.DoesNotExist, TicketAck.DoesNotExist):
            raise Http404
        return ack
    
    def delete(self, request, *args, **kwargs):
        ack = self.get_object()
        if not (self.ticket.can_edit(request.user) and ack.user_removable):
            return HttpResponseForbidden(_('You cannot edit this'))
        
        ack_display = ack.get_ack_type_display()
        ack.delete()
        
        msg = _('Ticket %(ticket_id)s confirmation "%(confirmation)s" has been deleted.') % {
            'ticket_id':self.ticket.id, 'confirmation':ack_display,
        }
        messages.success(request, msg)
        return HttpResponseRedirect(self.ticket.get_absolute_url())
ticket_ack_delete = TicketAckDeleteView.as_view()

def topic_list(request):
    return render(request, 'tracker/topic_list.html', {
        'open_topics': Topic.objects.filter(open_for_tickets=True),
        'closed_topics': Topic.objects.filter(open_for_tickets=False),
    })

class TopicDetailView(CommentPostedCatcher, DetailView):
    model = Topic
topic_detail = TopicDetailView.as_view()

def topics_js(request):
    data = {}
    for t in Topic.objects.all():
        data[t.id] = {}
        for attr in ('form_description', 'ticket_media', 'ticket_expenses'):
            data[t.id][attr] = getattr(t, attr)
    
    content = 'topics_table = %s;' % json.dumps(data)
    return HttpResponse(content, content_type='text/javascript')

class TicketForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TicketForm, self).__init__(*args, **kwargs)
        self.fields['topic'].queryset = self.get_topic_queryset()
    
    def get_topic_queryset(self):
        return Topic.objects.filter(open_for_tickets=True)

    def _media(self):
        return super(TicketForm, self).media + forms.Media(js=('ticketform.js', reverse('topics_js')))
    media = property(_media)

    class Meta:
        model = Ticket
        exclude = ('created', 'updated', 'sort_date', 'requested_user', 'requested_text',
            'custom_state', 'rating_percentage', 'supervisor_notes', 'cluster', 'payment_status', 'mandatory_report')
        widgets = {
            'event_date': adminwidgets.AdminDateWidget(),
            'summary': forms.TextInput(attrs={'size':'40'}),
            'description': forms.Textarea(attrs={'rows':'4', 'cols':'60'}),
        }

def check_ticket_form_deposit(ticketform, preexpeditures):
    """
    Checks ticket deposit form field against preexpediture form.
    Injects error there if there is a problem.
    """
    if not (ticketform.is_valid() and preexpeditures.is_valid()):
        return

    deposit = ticketform.cleaned_data.get('deposit')
    if deposit is None:
        return

    total_preexpeditures = sum([pe.cleaned_data.get('amount', 0) for pe in preexpeditures])
    if deposit > total_preexpeditures:
        ticketform.add_error('deposit', forms.ValidationError(
            _("Your deposit is bigger than your preexpeditures")
        ))


def get_edit_ticket_form_class(ticket):
    class EditTicketForm(TicketForm):
        def get_topic_queryset(self):
            return Topic.objects.filter(Q(open_for_tickets=True) | Q(id=ticket.topic.id))

    class PrecontentEditTicketForm(EditTicketForm):
        def __init__(self, *args, **kwargs):
            super(PrecontentEditTicketForm, self).__init__(*args, **kwargs)
            self.fields['deposit'].widget.attrs['disabled'] = True

    if "precontent" in ticket.ack_set():
        return PrecontentEditTicketForm
    else:
        return EditTicketForm

adminCore = forms.Media(js=(
    settings.ADMIN_MEDIA_PREFIX + "js/jquery.min.js",
    settings.STATIC_URL + "jquery.both.js",
    settings.ADMIN_MEDIA_PREFIX + "js/core.js",
    settings.ADMIN_MEDIA_PREFIX + "js/inlines.js",
))

class ExtraItemFormSet(BaseInlineFormSet):
    """
    Inline formset class patched to always have one extra form when bound.
    This prevents hiding of the b0rked field in the javascript-hidden area
    when validation fails.
    """
    def total_form_count(self):
        original_count = super(ExtraItemFormSet, self).total_form_count()
        if self.is_bound:
            return original_count + 1
        else:
            return original_count

MEDIAINFO_FIELDS = ('url', 'description', 'count')
def mediainfo_formfield(f, **kwargs):
    if f.name == 'url':
        kwargs['widget'] = forms.TextInput(attrs={'size':'60'})
    elif f.name == 'count':
        kwargs['widget'] = forms.TextInput(attrs={'size':'4'})
    return f.formfield(**kwargs)
mediainfoformset_factory = curry(inlineformset_factory, Ticket, MediaInfo,
    formset=ExtraItemFormSet, fields=MEDIAINFO_FIELDS, formfield_callback=mediainfo_formfield)

EXPEDITURE_FIELDS = ('description', 'amount', 'wage')
expeditureformset_factory = curry(inlineformset_factory, Ticket, Expediture,
    formset=ExtraItemFormSet, fields=EXPEDITURE_FIELDS)

PREEXPEDITURE_FIELDS = ('description', 'amount', 'wage')
preexpeditureformset_factory = curry(inlineformset_factory, Ticket, Preexpediture,
    formset=ExtraItemFormSet, fields=PREEXPEDITURE_FIELDS)

@login_required
def create_ticket(request):
    MediaInfoFormSet = mediainfoformset_factory(extra=2, can_delete=False)
    ExpeditureFormSet = expeditureformset_factory(extra=2, can_delete=False)
    PreexpeditureFormSet = preexpeditureformset_factory(extra=2, can_delete=False)
    
    if request.method == 'POST':
        ticketform = TicketForm(request.POST)
        try:
            mediainfo = MediaInfoFormSet(request.POST, prefix='mediainfo')
            expeditures = ExpeditureFormSet(request.POST, prefix='expediture')
            preexpeditures = PreexpeditureFormSet(request.POST, prefix='preexpediture')
            mediainfo.media   # trigger ValidationError when management form field are missing
            expeditures.media # this seems to be a regression between Django 1.3 and 1.6
            preexpeditures.media # test
        except forms.ValidationError, e:
            return HttpResponseBadRequest(unicode(e))
        
        check_ticket_form_deposit(ticketform, preexpeditures)
        if ticketform.is_valid() and mediainfo.is_valid() and expeditures.is_valid() and preexpeditures.is_valid():
            ticket = ticketform.save(commit=False)
            ticket.requested_user = request.user
            ticket.save()
            ticketform.save_m2m()
            if ticket.topic.ticket_media:
                mediainfo.instance = ticket
                mediainfo.save()
            if ticket.topic.ticket_expenses:
                expeditures.instance = ticket
                expeditures.save()
            if ticket.topic.ticket_preexpenses:
                preexpeditures.instance = ticket
                preexpeditures.save()
            
            messages.success(request, _('Ticket %s created.') % ticket)
            return HttpResponseRedirect(ticket.get_absolute_url())
    else:
        initial = {'event_date': datetime.date.today()}
        if 'topic' in request.GET:
            initial['topic'] = request.GET['topic']
        if 'ticket' in request.GET:
            ticket = get_object_or_404(Ticket, id=request.GET['ticket'])
            initial['summary'] = ticket.summary
            initial['topic'] = ticket.topic
            initial['description'] = ticket.description
            initial['deposit'] = ticket.deposit
        ticketform = TicketForm(initial=initial)
        mediainfo = MediaInfoFormSet(prefix='mediainfo')
        expeditures = ExpeditureFormSet(prefix='expediture')
        initialPreexpeditures = []
        if 'ticket' in request.GET:
            for pe in Preexpediture.objects.filter(ticket=ticket):
                initialPe = {}
                initialPe['description'] = pe.description
                initialPe['amount'] = pe.amount
                initialPe['wage'] = pe.wage
                initialPreexpeditures.append(initialPe)
        PreexpeditureFormSet = preexpeditureformset_factory(extra=2+len(initialPreexpeditures), can_delete=False)
        preexpeditures = PreexpeditureFormSet(prefix='preexpediture', initial=initialPreexpeditures)
    
    return render(request, 'tracker/create_ticket.html', {
        'ticketform': ticketform,
        'mediainfo': mediainfo,
        'expeditures': expeditures,
        'preexpeditures': preexpeditures,
        'form_media': adminCore + ticketform.media + mediainfo.media + expeditures.media,
    })

@login_required
def edit_ticket(request, pk):
    ticket = get_object_or_404(Ticket, id=pk)
    if not ticket.can_edit(request.user):
        return HttpResponseForbidden(_('You cannot edit this ticket.'))
    TicketEditForm = get_edit_ticket_form_class(ticket)

    MediaInfoFormSet = mediainfoformset_factory(extra=1, can_delete=True)
    ExpeditureFormSet = expeditureformset_factory(extra=1, can_delete=True)
    PreexpeditureFormSet = preexpeditureformset_factory(extra=1, can_delete=True)
    
    if request.method == 'POST':
        ticketform = TicketEditForm(request.POST, instance=ticket)
        try:
            mediainfo = MediaInfoFormSet(request.POST, prefix='mediainfo', instance=ticket)
            if 'content' not in ticket.ack_set():
                expeditures = ExpeditureFormSet(request.POST, prefix='expediture', instance=ticket)
            if 'precontent' not in ticket.ack_set():
                preexpeditures = PreexpeditureFormSet(request.POST, prefix='preexpediture', instance=ticket)
        except forms.ValidationError, e:
            return HttpResponseBadRequest(unicode(e))
        
        check_ticket_form_deposit(ticketform, preexpeditures)
        if ticketform.is_valid() and mediainfo.is_valid() and expeditures.is_valid() and preexpeditures.is_valid():
            ticket = ticketform.save()
            mediainfo.save()
            if 'content' not in ticket.ack_set():
                expeditures.save()
            if 'precontent' not in ticket.ack_set():
                preexpeditures.save()
                
            messages.success(request, _('Ticket %s saved.') % ticket)
            return HttpResponseRedirect(ticket.get_absolute_url())
    else:
        ticketform = TicketEditForm(instance=ticket)
        mediainfo = MediaInfoFormSet(prefix='mediainfo', instance=ticket)

        if 'content' not in ticket.ack_set():
            expeditures = ExpeditureFormSet(prefix='expediture', instance=ticket)
        else:
            expeditures = None # Hide expeditures in the edit form

        if 'precontent' not in ticket.ack_set():
            preexpeditures = PreexpeditureFormSet(prefix='preexpediture', instance=ticket)
        else:
            preexpeditures = None # Hide preexpeditures in the edit form
    
    form_media = adminCore + ticketform.media + mediainfo.media
    if 'content' not in ticket.ack_set():
        form_media += expeditures.media
    if 'precontent' not in ticket.ack_set():
        form_media += preexpeditures.media

    return render(request, 'tracker/edit_ticket.html', {
        'ticket': ticket,
        'ticketform': ticketform,
        'mediainfo': mediainfo,
        'expeditures': expeditures,
        'preexpeditures': preexpeditures,
        'form_media': form_media,
        'user_can_edit_documents': ticket.can_edit_documents(request.user),
    })

class UploadDocumentForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'size':'60'}))
    name = forms.RegexField(r'^[-_\.A-Za-z0-9]+\.[A-Za-z0-9]+$', error_messages={'invalid':ugettext_lazy('We need a sane file name, such as my-invoice123.jpg')}, widget=forms.TextInput(attrs={'size':'30'}))
    description = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'size':'60'}))

DOCUMENT_FIELDS = ('filename', 'description')
def document_formfield(f, **kwargs):
    if f.name == 'description':
        kwargs['widget'] = forms.TextInput(attrs={'size':'60'})
    return f.formfield(**kwargs)
documentformset_factory = curry(inlineformset_factory, Ticket, Document,
    fields=DOCUMENT_FIELDS, formfield_callback=document_formfield)

def document_view_required(access, ticket_id_field='pk'):
    """ Wrapper for document-accessing views (access=read|write)"""
    def actual_decorator(view):
        def wrapped_view(request, *args, **kwargs):
            from django.contrib.auth.views import redirect_to_login
            if not request.user.is_authenticated():
                return redirect_to_login(request.path)
            
            ticket = get_object_or_404(Ticket, id=kwargs[ticket_id_field])
            if (access == 'read' and ticket.can_see_documents(request.user)) or (access == 'write' and ticket.can_edit_documents(request.user)):
                return view(request, *args, **kwargs)
            else:
                return HttpResponseForbidden(_("You cannot see this ticket's documents."))
        return wrapped_view
    
    return actual_decorator
        
@document_view_required(access='write')
def edit_ticket_docs(request, pk):
    DocumentFormSet = documentformset_factory(extra=0, can_delete=True)
    
    ticket = get_object_or_404(Ticket, id=pk)
    if request.method == 'POST':
        try:
            documents = DocumentFormSet(request.POST, prefix='docs', instance=ticket)
        except forms.ValidationError, e:
            return HttpResponseBadRequest(unicode(e))
        
        if documents.is_valid():
            documents.save()
            messages.success(request, _('Document changes for ticket %s saved.') % ticket)
            return HttpResponseRedirect(ticket.get_absolute_url())
    else:
        documents = DocumentFormSet(prefix='docs', instance=ticket)
    
    return render(request, 'tracker/edit_ticket_docs.html', {
        'ticket': ticket,
        'documents': documents,
    })

@document_view_required(access='write')
def upload_ticket_doc(request, pk):
    ticket = get_object_or_404(Ticket, id=pk)
    
    if request.method == 'POST':
        upload = UploadDocumentForm(request.POST, request.FILES)
        if upload.is_valid():
            doc = Document(ticket=ticket)
            payload = upload.cleaned_data['file']
            filename = upload.cleaned_data['name']
            doc.filename = filename
            doc.size = payload.size
            doc.content_type = payload.content_type
            doc.description = upload.cleaned_data['description']
            doc.payload.save(filename, payload)
            doc.save()
            messages.success(request, _('File %(filename)s has been saved.') % {'filename':filename})
            
            if 'add-another' in request.POST:
                next_view = 'upload_ticket_doc'
            else:
                next_view = 'ticket_detail'
            return HttpResponseRedirect(reverse(next_view, kwargs={'pk':ticket.id}))
    else:
        upload = UploadDocumentForm()
    
    return render(request, 'tracker/upload_ticket_doc.html', {
        'ticket': ticket,
        'upload': upload,
        'form_media': adminCore + upload.media,
    })

@document_view_required(access='read', ticket_id_field='ticket_id')
def download_document(request, ticket_id, filename):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    doc = ticket.document_set.get(filename=filename)
    return sendfile(request, doc.payload.path, mimetype=doc.content_type)

def topic_finance(request):
    grants_out = []
    for grant in Grant.objects.all():
        topics = []
        grant_finance = FinanceStatus()
        for topic in grant.topic_set.all():
            topic_finance = topic.payment_summary()
            grant_finance.add_finance(topic_finance)
            topics.append({'topic':topic, 'finance':topic_finance})
        grants_out.append({'grant':grant, 'topics':topics, 'finance':grant_finance, 'rows':len(topics)+1})
    
    csums = Cluster.cluster_sums()
    return render(request, 'tracker/topic_finance.html', {
        'grants': grants_out,
        'cluster_sums': csums,
        'total_transactions': csums['paid'] + csums['overpaid'], 
        'have_fuzzy': any([row['finance'].fuzzy for row in grants_out]),
    })

class HttpResponseCsv(HttpResponse):
    def __init__(self, fields, *args, **kwargs):
        kwargs['content_type'] = 'text/csv'
        super(HttpResponseCsv, self).__init__(*args, **kwargs)
        self.writerow(fields)

    def writerow(self, row):
        self.write(u';'.join(map(lambda s: unicode(s).replace(';', ',').replace('\n', ' '), row)))
        self.write(u'\r\n')

def get_tickets_filtered(fields, **kwargs):
	tickets = Ticket.objects.filter(kwargs)
	resp = HttpResponseCsv(fields)
	for ticket in tickets:
		dictticket = ticket.__dict__
		row = []
		for field in fields:
			row.append(dictticket[field])
		resp.writerow(row)
	return resp

def _get_topic_content_acks_per_user():
    """ Returns content acks counts per user and topic """
    cursor = connection.cursor()
    cursor.execute("""
        select
            ack.added_by_id user_id, topic.grant_id grant_id, ticket.topic_id topic_id, count(1) ack_count
        from
            tracker_ticketack ack
            left join tracker_ticket ticket on ack.ticket_id = ticket.id
            left join tracker_topic topic on ticket.topic_id = topic.id
        where
            ack_type = 'content'
            and added_by_id is not null
        group by user_id, grant_id, topic_id order by user_id, grant_id, topic_id
    """)
    row_tuple_type = namedtuple('Result', [col[0] for col in cursor.description])
    result = [row_tuple_type(*row) for row in cursor]
    users = User.objects.in_bulk([r.user_id for r in result])
    grants = Grant.objects.in_bulk([r.grant_id for r in result])
    topics = Topic.objects.in_bulk([r.topic_id for r in result])

    final_row_type = namedtuple('AckRow', ('user', 'grant', 'topic', 'ack_count'))
    return [
        final_row_type(UserWrapper(users.get(r.user_id)), grants.get(r.grant_id), topics.get(r.topic_id), r.ack_count)
        for r in result
    ]

def topic_content_acks_per_user(request):
    return render(request, 'tracker/topic_content_acks_per_user.html', {
        'acks': _get_topic_content_acks_per_user(),
    })

def topic_content_acks_per_user_csv(request):
    response = HttpResponseCsv(['user', 'grant', 'topic', 'ack_count'])
    for row in _get_topic_content_acks_per_user():
        response.writerow([row.user, row.grant, row.topic, row.ack_count])
    return response

def transaction_list(request):
    return render(request, 'tracker/transaction_list.html', {
        'transaction_list': Transaction.objects.all(),
        'total': Transaction.objects.aggregate(amount=models.Sum('amount'))['amount'],
    })



def transactions_csv(request):
    response = HttpResponseCsv(
        ['DATE', 'OTHER PARTY', 'AMOUNT ' + unicode(settings.TRACKER_CURRENCY), 'DESCRIPTION', 'TICKETS', 'GRANTS', 'ACCOUNTING INFO']
    )
    
    for tx in Transaction.objects.all():
        response.writerow([
            tx.date.strftime('%Y-%m-%d'),
            tx.other_party(),
            tx.amount,
            tx.description,
            u' '.join([unicode(t.id) for t in tx.tickets.all()]),
            u' '.join([g.short_name for g in tx.grant_set()]),
            tx.accounting_info,
        ])
    return response

def user_list(request):
    totals = {
        'ticket_count': Ticket.objects.count(),
        'media': MediaInfo.objects.aggregate(objects=models.Count('id'), media=models.Sum('count')),
        'accepted_expeditures': sum([t.accepted_expeditures() for t in Ticket.objects.filter(rating_percentage__gt=0)]),
        'transactions': Transaction.objects.aggregate(amount=models.Sum('amount'))['amount'],
    }
    
    userless = Ticket.objects.filter(requested_user=None)
    if userless.count() > 0:
        unassigned = {
            'ticket_count': userless.count(),
            'media': MediaInfo.objects.extra(where=['ticket_id in (select id from tracker_ticket where requested_user_id is null)']).aggregate(objects=models.Count('id'), media=models.Sum('count')),
            'accepted_expeditures': sum([t.accepted_expeditures() for t in userless]),
        }
    else:
        unassigned = None
    
    return render(request, 'tracker/user_list.html', {
        'user_list': User.objects.all(),
        'unassigned': unassigned,
        'totals': totals,
    })

def user_detail(request, username):
    user = get_object_or_404(User, username=username)
    
    return render(request, 'tracker/user_detail.html', {
        'user_obj': user,
        # ^ NOTE 'user' means session user in the template, so we're using user_obj
        'ticket_list': user.ticket_set.all(),
    })

class UserDetailsChange(FormView):
    template_name = 'tracker/user_details_change.html'
    user_fields = ('first_name', 'last_name', 'email')
    profile_fields = [f.name for f in TrackerProfile._meta.fields if f.name not in ('id', 'user')]
    
    def make_user_details_form(self):
        fields = fields_for_model(User, fields=self.user_fields)
        fields.update(fields_for_model(TrackerProfile, exclude=('user', )))
        return type('UserDetailsForm', (forms.BaseForm,), { 'base_fields': fields })
    
    def get_form_class(self):
        return self.make_user_details_form()
    
    def get_initial(self):
        user = self.request.user
        out = {}
        for f in self.user_fields:
            out[f] = getattr(user, f)
        for f in self.profile_fields:
            out[f] = getattr(user.trackerprofile, f)
        return out
    
    def form_valid(self, form):
        user = self.request.user
        for f in self.user_fields:
            setattr(user, f, form.cleaned_data[f])
        user.save()
        
        profile = user.trackerprofile
        for f in self.profile_fields:
            setattr(profile, f, form.cleaned_data[f])
        profile.save()
        
        messages.success(self.request, _('Your details have been saved.'))
        return HttpResponseRedirect(reverse('index'))
        
user_details_change = login_required(UserDetailsChange.as_view())

def cluster_detail(request, pk):
    id = int(pk)
    try:
        cluster = Cluster.objects.get(id=id)
    except Cluster.DoesNotExist:
        try:
            ticket = Ticket.objects.get(id=id)
            if ticket.cluster is None:
                raise Http404
            return HttpResponseRedirect(reverse('cluster_detail', kwargs={'pk':ticket.cluster.id}))
        except Ticket.DoesNotExist:
            raise Http404
    
    return render(request, 'tracker/cluster_detail.html', {
        'cluster': cluster,
        'ticket_summary': {'accepted_expeditures': cluster.total_tickets},
    })
    

class AdminUserListView(ListView):
    model = User
    template_name = 'tracker/admin_user_list.html'
    
    def get_context_data(self, **kwargs):
            context = super(AdminUserListView, self).get_context_data(**kwargs)
            context['is_tracker_supervisor'] = self.request.user.has_perm('tracker.supervisor')
            return context
admin_user_list = login_required(AdminUserListView.as_view())

def export(request):
    return render(request, 'tracker/export.html', {})
