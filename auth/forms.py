# -*- encoding: utf-8 -*-
# vim:encoding=utf-8:

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _

class AuthForm(AuthenticationForm):
    """
    Class for authenticating users on email/password credentials.
    """
    username = forms.EmailField(label=_("Email"), max_length=75)
    remember = forms.BooleanField( label=_("Remember me on this computer"), 
            required=False)
