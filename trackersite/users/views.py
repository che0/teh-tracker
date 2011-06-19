# -*- coding: utf-8 -*-
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'users/register.html'
    
    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'User %s created.' % form.cleaned_data['username'])
        return HttpResponseRedirect(reverse('ticket_list'))
register = RegisterView.as_view()
