# -*- coding: utf-8 -*-
from django.forms import ModelForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.generic import CreateView
from django.utils.translation import ugettext as _

from tracker.models import Ticket

class CreateTicketForm(ModelForm):
    class Meta:
        model = Ticket
        exclude = ('created', 'updated', 'requested_by', 'status')

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
