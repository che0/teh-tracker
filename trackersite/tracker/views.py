# -*- coding: utf-8 -*-
from django.forms import ModelForm, ModelChoiceField, ValidationError
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.generic import CreateView
from django.utils.translation import ugettext as _

from tracker.models import Ticket, Topic

class CreateTicketForm(ModelForm):
    def clean_topic(self):
        topic = self.cleaned_data['topic']
        if not topic.open_for_tickets:
            raise ValidationError(_("Select an open topic. This ticket is not open for ticket submissions."))
        return topic
    
    class Meta:
        model = Ticket
        exclude = ('created', 'updated', 'requested_by', 'status')
        widgets = {
            'topic_id': ModelChoiceField(Topic.objects.filter(open_for_tickets=True)),
        }

class CreateTicketView(CreateView):
    form_class = CreateTicketForm
    template_name = 'tracker/create_ticket.html'
    
    def form_valid(self, form):
        ticket = form.save(commit=False)
        ticket.requested_by = self.request.user.username
        ticket.status = 'new'
        ticket.save()
        form.save_m2m()
        messages.success(self.request, _('Ticket %s created.') % ticket)
        return HttpResponseRedirect(ticket.get_absolute_url())
create_ticket = login_required(CreateTicketView.as_view())
