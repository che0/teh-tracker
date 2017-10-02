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
        for attr in ('form_description', 'ticket_media', 'ticket_expenses', 'ticket_preexpenses'):
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
        """ Ticket edit form with disabled deposit field """
        # NOTE in Django 1.9+, this can be set directly on the field:
        # https://docs.djangoproject.com/en/dev/ref/forms/fields/#disabled
        def __init__(self, *args, **kwargs):
            super(PrecontentEditTicketForm, self).__init__(*args, **kwargs)
            self.fields['deposit'].widget.attrs['disabled'] = True
            self.fields['deposit'].required = False

        def clean_deposit(self):
            return self.instance.deposit

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
            else:
                expeditures = None
            if 'precontent' not in ticket.ack_set():
                preexpeditures = PreexpeditureFormSet(request.POST, prefix='preexpediture', instance=ticket)
            else:
                preexpeditures = None
        except forms.ValidationError, e:
            return HttpResponseBadRequest(unicode(e))
        
        if 'precontent' not in ticket.ack_set():
            check_ticket_form_deposit(ticketform, preexpeditures)

        if ticketform.is_valid() and mediainfo.is_valid() \
                and (expeditures.is_valid() if 'content' not in ticket.ack_set() else True) \
                and (preexpeditures.is_valid() if 'precontent' not in ticket.ack_set() else True):
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
        self.write(u';'.join(map(lambda s: u'"' + unicode(s).replace('"', "'") + u'"', row)))
        self.write(u'\r\n')

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
        'transactions': Expediture.objects.filter(paid=True).aggregate(amount=models.Sum('amount'))['amount'],
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
    if request.method == 'POST':
        typ = request.POST['type']
        if typ == 'ticket':
            states = ['draft', 'wfpreapproval', 'wfsubmiting', 'wfapproval', 'wfdocssub', 'wffill', 'complete', 'archived', 'closed', 'custom']
            tickets = []
            for state in states:
                if state in request.POST:
                    tickets += Ticket.get_tickets_with_state(request.POST[state])
            if len(tickets) == 0:
                tickets = list(Ticket.objects.all())
            tickets = list(set(tickets))
            topics = []
            for item in request.POST:
                if item.startswith('ticket-topic-'):
                    topics.append(Topic.objects.get(id=long(request.POST[item])))
            tmp = []
            if len(topics) != 0:
                for topic in topics:
                    for ticket in tickets:
                        if ticket.topic == topic:
                            tmp.append(ticket)
                tickets = tmp
                tmp = []
            users = []
            for item in request.POST:
                if item.startswith('ticket-user-'):
                    users.append(User.objects.get(id=long(request.POST[item])))
            if len(users) != 0:
                for user in users:
                    for ticket in tickets:
                        if ticket.requested_user == user:
                            tmp.append(ticket)
                    tickets = tmp
                    tmp = []
            larger = request.POST['preexpeditures-larger']
            smaller = request.POST['preexpeditures-smaller']
            if larger != '' and smaller != '':
                larger = int(larger)
                smaller = int(smaller)
                for ticket in tickets:
                    real = ticket.preexpeditures()['amount']
                    if real == None:
                        real = 0
                    if real >= larger and real <= smaller:
                        tmp.append(ticket)
                tickets = tmp
                tmp = []
            elif larger != '' and smaller == '':
                larger = int(larger)
                for ticket in tickets:
                    real = ticket.preexpeditures()['amount']
                    if real == None:
                        real = 0
                    if real >= larger:
                        tmp.append(ticket)
                tickets = tmp
                tmp = []
            elif larger == '' and smaller != '':
                smaller = int(smaller)
                for ticket in tickets:
                    real = ticket.preexpeditures()['amount']
                    if real == None:
                        real = 0
                    if real <= smaller:
                        tmp.append(ticket)
                tickets = tmp
                tmp = []
            larger = request.POST['expeditures-larger']
            smaller = request.POST['expeditures-smaller']
            if larger != '' and smaller != '':
                larger = int(larger)
                smaller = int(smaller)
                for ticket in tickets:
                    real = ticket.expeditures()['amount']
                    if real == None:
                        real = 0
                    if real >= larger and real <= smaller:
                        tmp.append(ticket)
                tickets = tmp
                tmp = []
            elif larger != '' and smaller == '':
                larger = int(larger)
                for ticket in tickets:
                    real = ticket.expeditures()['amount']
                    if real == None:
                        real = 0
                    if real >= larger:
                        tmp.append(ticket)
                tickets = tmp
                tmp = []
            elif larger == '' and smaller != '':
                smaller = int(smaller)
                for ticket in tickets:
                    real = ticket.expeditures()['amount']
                    if real == None:
                        real = 0
                    if real <= smaller:
                        tmp.append(ticket)
                tickets = tmp
                tmp = []
            larger = request.POST['acceptedexpeditures-larger']
            smaller = request.POST['acceptedexpeditures-smaller']
            if larger != '' and smaller != '':
                larger = int(larger)
                smaller = int(smaller)
                for ticket in tickets:
                    real = ticket.accepted_expeditures()
                    if real >= larger and real <= smaller:
                        tmp.append(ticket)
                tickets = tmp
                tmp = []
            elif larger != '' and smaller == '':
                larger = int(larger)
                for ticket in tickets:
                    real = ticket.accepted_expeditures()
                    if real >= larger:
                        tmp.append(ticket)
                tickets = tmp
                tmp = []
            elif larger == '' and smaller != '':
                smaller = int(smaller)
                for ticket in tickets:
                    real = ticket.accepted_expeditures()
                    if real <= smaller:
                        tmp.append(ticket)
                tickets = tmp
                tmp = []
            mandatory_report = 'ticket-report-mandatory' in request.POST
            if mandatory_report:
                tmp = []
                for ticket in tickets:
                    if ticket.mandatory_report:
                        tmp.append(ticket)
                tickets = tmp
                del(tmp)
            response = HttpResponseCsv(['id', 'created', 'updated', 'event_date', 'event_url', 'summary', 'requested_by', 'grant', 'topic', 'state', 'deposit', 'description', 'mandatory_report', 'accepted_expeditures', 'preexpeditures', 'expeditures'])
            response['Content-Disposition'] = 'attachment; filename="exported-tickets.csv"'
            for ticket in tickets:
                response.writerow([ticket.id, ticket.created, ticket.updated, ticket.event_date, ticket.event_url, ticket.summary, ticket.requested_by(), ticket.topic.grant.full_name, ticket.topic.name, ticket.state_str(), ticket.deposit, ticket.description, ticket.mandatory_report, ticket.accepted_expeditures(), ticket.preexpeditures()['amount'], ticket.expeditures()['amount']])
            return response
        elif typ == 'grant':
            response = HttpResponseCsv(['full_name', 'short_name', 'slug', 'description'])
            grants = Grant.objects.all()
            for grant in grants:
                response.writerow([grant.full_name, grant.short_name, grant.slug, grant.description])
            return response
        elif typ == 'preexpediture':
            larger = request.POST['preexpediture-amount-larger']
            smaller = request.POST['preexpediture-amount-larger']
            wage = 'preexpediture-wage' in request.POST
            if larger != '' and smaller != '':
                larger = int(larger)
                smaller = int(smaller)
                preexpeditures = Preexpediture.objects.filter(amount__gte=larger, amount__lte=smaller, wage=wage)
            elif larger != '' and smaller == '':
                larger = int(larger)
                preexpeditures = Preexpediture.objects.filter(amount__gte=larger, wage=wage)
            elif larger == '' and smaller != '':
                smaller = int(smaller)
                preexpeditures = Preexpediture.objects.filter(amount__lte=smaller, wage=wage)
            else:
                preexpeditures = Preexpediture.objects.filter(wage=wage)
            response = HttpResponseCsv(['ticket_id', 'description', 'amount', 'wage'])
            response['Content-Disposition'] = 'attachment; filename="exported-preexpeditures.csv"'
            for preexpediture in preexpeditures:
                response.writerow([preexpediture.ticket_id, preexpediture.description, preexpediture.amount, preexpediture.wage])
            return response
        elif typ == 'expediture':
            larger = request.POST['expediture-amount-larger']
            smaller = request.POST['expediture-amount-smaller']
            wage = 'expediture-wage' in request.POST
            paid = 'expediture-paid' in request.POST
            if larger != '' and smaller != '':
                larger = int(larger)
                smaller = int(smaller)
                expeditures = Expediture.objects.filter(amount__gte=larger, amount__lte=smaller, wage=wage, paid=paid)
            elif larger != '' and smaller == '':
                larger = int(larger)
                expeditures = Expediture.objects.filter(amount__gte=larger, wage=wage, paid=paid)
            elif larger == '' and smaller != '':
                smaller = int(smaller)
                expeditures = Expediture.objects.filter(amount__lte=smaller, wage=wage, paid=paid)
            else:
                expeditures = Expediture.objects.filter(wage=wage, paid=paid)
            response = HttpResponseCsv(['ticket_id', 'description', 'amount', 'wage', 'paid'])
            response['Content-Disposition'] = 'attachment; filename="exported-expeditures.csv"'
            for expediture in expeditures:
                response.writerow([expediture.ticket_id, expediture.description, expediture.amount, expediture.wage, expediture.paid])
            return response
        elif typ == 'topic':
            users = []
            for item in request.POST:
                if item.startswith('topics-user-'):
                    users.append(User.objects.get(id=long(request.POST[item])))
            topics = Topic.objects.all()
            if len(users) != 0:
                tmp = []
                for user in users:
                    for topic in topics:
                        if user in topic.admin.all():
                            tmp.append(topic)
                topics = list(set(tmp))
                tmp = []
            larger = request.POST['topics-tickets-larger']
            smaller = request.POST['topics-tickets-smaller']
            if larger != '' and smaller != '':
                larger = int(larger)
                smaller = int(smaller)
                tmp = []
                for topic in topics:
                    if topic.ticket_set.count >= larger and topic.ticket_set.count <= smaller:
                        tmp.append(topic)
                topics = tmp
                tmp = []
            elif larger != '' and smaller == '':
                larger = int(larger)
                tmp = []
                for topic in topics:
                    if topic.ticket_set.count >= larger:
                        tmp.append(topic)
                topics = tmp
                tmp = []
            elif larger == '' and smaller != '':
                smaller = int(smaller)
                tmp = []
                for topic in topics:
                    if topic.ticket_set.count <= smaller:
                        tmp.append(topic)
                topics = tmp
                tmp = []
            if request.POST['topics-paymentstate'] != 'default':
                paymentstatus = request.POST['topics-paymentstate']
                larger = request.POST['topics-paymentstate-larger']
                smaller = request.POST['topics-paymentstate-smaller']
                if larger != '' and smaller != '':
                    larger = int(larger)
                    smaller = int(smaller)
                    tmp = []
                    for topic in topics:
                        number = -1
                        if paymentstatus in topic.tickets_per_payment_status():
                            number = topic.tickets_per_payment_status()[paymentstatus]
                        else:
                            number = 0
                        if number >= larger and number <= smaller:
                            tmp.append(topic)
                    topics = tmp
                    del(tmp)
                elif larger != '' and smaller == '':
                    larger = int(larger)
                    tmp = []
                    for topic in topics:
                        number = -1
                        if paymentstatus in topic.tickets_per_payment_status():
                            number = topic.tickets_per_payment_status()[paymentstatus]
                        else:
                            number = 0
                        if number >= larger:
                            tmp.append(topic)
                    topics = tmp
                    del(tmp)
                elif larger == '' and smaller != '':
                    smaller = int(smaller)
                    tmp = []
                    for topic in topics:
                        number = -1
                        if paymentstatus in topic.tickets_per_payment_status():
                            number = topic.tickets_per_payment_status()[paymentstatus]
                        else:
                            number = 0
                        if number <= smaller:
                            tmp.append(topic)
                    topics = tmp
                    del(tmp)
            response = HttpResponseCsv(['name', 'grant', 'open_for_new_tickets', 'media', 'expenses', 'preexpenses', 'description', 'form_description', 'admins'])
            response['Content-Disposition'] = 'attachment; filename="exported-topics.csv"'
            for topic in topics:
                names = []
                for ad in topic.admin.all():
                    names.append(ad.username)
                admins = ", ".join(names)
                response.writerow([topic.name, topic.grant.full_name, topic.open_for_tickets, topic.ticket_media, topic.ticket_expenses, topic.ticket_preexpenses, topic.description, topic.form_description, admins])
            return response
        elif typ == 'user':
            if request.user.is_authenticated():
                if request.user.is_staff:
                    users = TrackerProfile.objects.all()
                    larger = request.POST['users-created-larger']
                    smaller = request.POST['users-created-smaller']
                    if larger != '' and smaller != '':
                        larger = int(larger)
                        smaller = int(smaller)
                        tmp = []
                        for user in users:
                            real = user.count_ticket_created()
                            if real >= larger and real <= smaller:
                                tmp.append(user)
                        users = tmp
                        del(tmp)
                    elif larger != '' and smaller == '':
                        larger = int(larger)
                        tmp = []
                        for user in users:
                            real = user.count_ticket_created()
                            if real >= larger:
                                tmp.append(user)
                        users = tmp
                        del(tmp)
                    elif larger == '' and smaller != '':
                        smaller = int(smaller)
                        tmp = []
                        for user in users:
                            real = user.count_ticket_created()
                            if real <= smaller:
                                tmp.append(user)
                        users = tmp
                        del(tmp)
                    larger = request.POST['users-accepted-larger']
                    smaller = request.POST['users-accepted-smaller']
                    if larger != '' and smaller != '':
                        larger = int(larger)
                        smaller = int(smaller)
                        tmp = []
                        for user in users:
                            real = user.accepted_expeditures()
                            if real >= larger and real <= smaller:
                                tmp.append(user)
                        users = tmp
                        del(tmp)
                    elif larger != '' and smaller == '':
                        larger = int(larger)
                        tmp = []
                        for user in users:
                            real = user.accepted_expeditures()
                            if real >= larger:
                                tmp.append(user)
                        users = tmp
                        del(tmp)
                    elif larger == '' and smaller != '':
                        smaller = int(smaller)
                        tmp = []
                        for user in users:
                            real = user.accepted_expeditures()
                            if real <= smaller:
                                tmp.append(user)
                        users = tmp
                        del(tmp)
        
                    larger = request.POST['users-paid-larger']
                    smaller = request.POST['users-paid-larger']
                    if larger != '' and smaller != '':
                        larger = int(larger)
                        smaller = int(larger)
                        tmp = []
                        for user in users:
                            real = user.paid_expeditures()
                            if real >= larger and real <= smaller:
                                tmp.append(user)
                        users = tmp
                        del(tmp)
                    elif larger != '' and smaller == '':
                        larger = int(larger)
                        tmp = []
                        for user in users:
                            real = user.paid_expeditures()
                            if real >= larger:
                                tmp.append(user)
                        users = tmp
                        del(tmp)
                    elif larger == '' and smaller != '':
                        smaller = int(smaller)
                        tmp = []
                        for user in users:
                            real = user.paid_expeditures()
                            if real <= smaller:
                                tmp.append(user)
                            users = tmp
                            del(tmp)
        
                    if 'user-permision' in request.POST:
                        priv = request.POST['user-permision']
                        tmp = []
                        if priv == 'normal':
                            for user in users:
                                if not user.user.is_staff and not user.user.is_superuser:
                                    tmp.append(user)
                        elif priv == 'staff':
                            for user in users:
                                if user.user.is_staff:
                                    tmp.append(user)
                        elif priv == 'superuser':
                            for user in users:
                                if user.user.is_superuser:
                                    tmp.append(user)
                        else:
                            return HttpResponseBadRequest('You must fill the form validly')
                        users = tmp
                        del(tmp)
            
                    response = HttpResponseCsv(['id', 'username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'date_joined', 'created_tickets', 'accepted_expeditures', 'paid_expeditures', 'bank_account', 'other_contact', 'other_identification'])
                    response['Content-Disposition'] = 'attachment; filename="exported-users.csv"'
                    for user in users:
                        response.writerow([user.user.id, user.user.username, user.user.first_name, user.user.last_name, user.user.email, user.user.is_active, user.user.is_staff, user.user.is_superuser, user.user.last_login, user.user.date_joined, user.count_ticket_created(), user.accepted_expeditures(), user.paid_expeditures(), user.bank_account, user.other_contact, user.bank_account])
                    return response
            return HttpResponseForbidden(_('You must be staffer in order to export users'))

        return HttpResponseBadRequest(_('You must fill the form validly'))
    else:
        return render(
            request,
            'tracker/export.html',
            {
                'topics': Topic.objects.all(),
                'users': User.objects.all(),
                'tickets': Ticket.objects.all(),
            })

@login_required
def importcsv(request):
    if request.method == 'POST' and not request.FILES['csvfile']:
        return render(request, 'tracker/import.html', {})
    elif request.method == 'POST' and request.FILES['csvfile']:
        csvfile = request.FILES['csvfile']
        header = None
        if request.POST['type'] == 'ticket':
            for chunk in csvfile.chunks():
                lines = chunk.split('\n')
                lines.pop()
                for lineraw in lines:
                    line = lineraw.split(';')
                    if not header:
                        header = line
                        continue
                    event_date = line[header.index('event_date')]
                    summary = line[header.index('summary')]
                    topic = Topic.objects.get(name=line[header.index('topic')])
                    event_url = line[header.index('event_url')]
                    description = line[header.index('description')]
                    deposit = float(line[header.index('deposit')])
                    ticket = Ticket.objects.create(event_date=event_date, summary=summary, topic=topic, event_url=event_url, description=description, deposit=deposit)
                    ticket.requested_user = request.user
                    ticket.save()
        elif request.POST['type'] == 'topic':
            if not request.user.is_staff:
                return HttpResponseForbidden(_('You must be staffer in order to be able import topics.'))
            for chunk in csvfile.chunks():
                lines = chunk.split('\n')
                lines.pop()
                for lineraw in lines:
                    line = lineraw.split(',')
                    if not header:
                        header = line
                        continue
                    name = line[header.index('name')]
                    grant = Grant.objects.get(full_name=line[header.index('grant')]).id
                    new_tickets = line[header.index('new_tickets')]
                    media = line[header.index('media')]
                    preexpenses = line[header.index('preexpenses')]
                    expenses = line[header.index('expenses')]
                    description = line[header.index('description')]
                    form_description = line[header.index('form_description')]
                    topic = Topic.objects.create(name=name, grant_id=grant, open_for_tickets=new_tickets, ticket_media=media, ticket_preexpenses=preexpenses, ticket_expenses=expenses, description=description, form_description=form_description)
                    adminsraw = line[header.index('admins')].split(';')
                    for admin in adminsraw:
                        topic.admin.add(User.objects.get(username=admin).id)
        elif request.POST['type'] == 'grant':
            if not request.user.is_staff:
                return HttpResponseForbidden(_('You must be staffer in order to be able import grants.'))
            for chunk in csvfile.chunks():
                lines = chunk.split('\n')
                lines.pop()
                for lineraw in lines:
                    line = lineraw.split(';')
                    if not header:
                        header = line
                        continue
                    full_name = line[header.index('full_name')]
                    short_name = line[header.index('short_name')]
                    slug = line[header.index('slug')]
                    description = line[header.index('description')]
                    grant = Grant.objects.create(full_name=full_name, short_name=short_name, slug=slug, description=description)
        elif request.POST['type'] == 'expense':
            for chunk in csvfile.chunks():
                lines = chunk.split('\n')
                lines.pop()
                for lineraw in lines:
                    line = lineraw.split(';')
                    if not header:
                        header = line
                        continue
                    ticket = Ticket.objects.get(id=line[header.index('ticket_id')])
                    description = line[header.index('description')]
                    amount = line[header.index('amount')]
                    wage = int(line[header.index('wage')])
                    if request.user.is_staff:
                        accounting_info = line[header.index('accounting_info')]
                        paid = int(line[header.index('paid')])
                    else:
                        accounting_info = ''
                        paid = 0
                    if ticket.can_edit(request.user) or request.user.is_staff:
                        expediture = Expediture.objects.create(ticket=ticket, description=description, amount=amount, wage=wage, accounting_info=accounting_info, paid=paid)
                    else:
                        return HttpResponseForbidden(_("You can't add expenses to ticket that you did not created."))
        elif request.POST['type'] == 'preexpense':
            for chunk in csvfile.chunks():
                lines = chunk.split('\n')
                lines.pop()
                for lineraw in lines:
                    line = lineraw.split(';')
                    if not header:
                        header = line
                        continue
                    ticket = Ticket.objects.get(id=line[header.index('ticket_id')])
                    description = line[header.index('description')]
                    amount = line[header.index('amount')]
                    wage = int(line[header.index('wage')])
                    if ticket.can_edit(request.user) or request.user.is_staff:
                        expediture = Preexpediture.objects.create(ticket=ticket, description=description, amount=amount, wage=wage)
                    else:
                        return HttpResponseForbidden(_("You can't add preexpenses to ticket that you did not created."))
        elif request.POST['type'] == 'user':
            if not request.user.is_superuser:
                return HttpResponseForbidden(_('You must be superuser in order to be able import users.'))
            for chunk in csvfile.chunks():
                lines = chunk.split('\n')
                lines.pop()
            for lineraw in lines:
                line = lineraw.split(';')
                if not header:
                    header = line
                    continue
                username = line[header.index('username')]
                password = line[header.index('password')]
                first_name = line[header.index('first_name')]
                last_name = line[header.index('last_name')]
                is_superuser = int(line[header.index('is_superuser')])
                is_staff = int(line[header.index('is_staff')])
                is_active = int(line[header.index('is_active')])
                email = line[header.index('email')]
                user = User.objects.create_user(username=username, password=password, email=email)
                user.first_name = first_name
                user.last_name = last_name
                user.is_superuser = is_superuser
                user.is_staff = is_staff
                user.is_active = is_active
                user.save()
        else:
            return render(request, 'tracker/import.html', {})
        return HttpResponseRedirect(reverse('index'))
    else:
        if 'examplefile' in request.GET:
            giveexample = request.GET['examplefile']
            if giveexample == 'ticket':
                response = HttpResponseCsv(['event_date', 'summary', 'topic', 'event_url', 'description', 'deposit'])
                response['Content-Disposition'] = 'attachment; filename="example-ticket.csv"'
                response.writerow([u'23. 4. 2010', u'Název ticketu', u'Název tématu', u'http://wikimedia.cz', u'Popis ticketu', u'Požadovaná záloha'])
                return response
            elif giveexample == 'topic':
                response = HttpResponseCsv(['name', 'grant', 'new_tickets', 'media', 'preexpenses', 'expenses', 'description', 'form_description'])
                response['Content-Disposition'] = 'attachment; filename="example-topic.csv"'
                response.writerow([u'Jméno tématu', u'Název grantu', u'True/False', u'True/False', u'True/False', u'True/False', u'Popis tématu', u'Popis formuláře tématu'])
                return response
            elif giveexample == 'grant':
	    	response = HttpResponseCsv(['full_name', 'short_name', 'slug', 'description'])
                response['Content-Disposition'] = 'attachment; filename="example-grant.csv"'
		response.writerow([u'Plné jméno', u'Krátké jméno', u'Slug', u'Popis'])
		return response
	    elif giveexample == 'expense':
                fields = ['ticket_id', 'description', 'amount', 'wage']
                if request.user.is_staff:
                    fields.append('accounting_info')
                    fields.append('paid')
                response = HttpResponseCsv(fields)
                response['Content-Disposition'] = 'attachment; filename="example-expense.csv"'
                row = [u'ID tiketu', u'Popis výdaje', u'Vydané peníze v CZK', u'True/False']
                if request.user.is_staff:
                    row.append(u'Účetní údaje')
                    row.append(u'True/False')
                response.writerow(row)
                return response
            elif giveexample == 'preexpense':
                response = HttpResponseCsv(['ticket_id', 'description', 'amount', 'wage'])
                response['Content-Disposition'] = 'attachment; filename="example-preexpense.csv"'
                response.writerow([u'ID tiketu', u'Popis výdaje', u'Vydané peníze v CZK', u'True/False'])
                return response
            elif giveexample == 'user':
                response = HttpResponseCsv(['username', 'password', 'first_name', 'last_name', 'is_superuser', 'is_staff', 'is_active', 'email'])
                response['Content-Disposition'] = 'attachment; filename="example-user.csv"'
                response.writerow([u'Uživatelské jméno', u'Heslo', u'KřestníJméno', u'Příjmení', u'True/False', u'True/False', u'True/False', u'emailova@adresa.cz'])
                return response
            else:
                return HttpResponseBadRequest("You can't want example file of invalid object")
        else:
            return render(request, 'tracker/import.html', {})
