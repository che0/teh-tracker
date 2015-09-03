# -*- coding: utf-8 -*-
from django.contrib import auth
from django.views.generic import CreateView
from django.contrib import messages
from django import forms
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget

class UserWithEmailForm(auth.forms.UserCreationForm):
    email = forms.EmailField(required=False, help_text=_("Will be used for password recovery and notifications, if you enable them."))
    captcha = ReCaptchaField(widget=ReCaptchaWidget())
    
    class Meta:
        model = auth.models.User
        fields = ("username", "email")
        # ^ UserCreationForm has custom handling of password

class RegisterView(CreateView):
    form_class = UserWithEmailForm
    template_name = 'users/register.html'
    
    def form_valid(self, form):
        form.save()
        messages.success(self.request, _('User %s created.') % form.cleaned_data['username'])
        return HttpResponseRedirect(reverse('ticket_list'))
register = RegisterView.as_view()
