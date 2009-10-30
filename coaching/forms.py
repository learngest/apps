# -*- encoding: utf-8 -*-

from django import forms
from django.utils.translation import ugettext as _
from django.contrib.admin import widgets
from django.conf import settings

from coaching.models import Utilisateur

class UtilisateurChangeForm(forms.ModelForm):
    """
    Modif de son propre profil par un Utilisateur
    Les champs que l'Utilisateur peut changer sont :
    - email
    - password
    - langue
    """
    new_password1 = forms.CharField(max_length=15, min_length=5,
            required=False,
            widget=forms.PasswordInput,
            label=_("New password"),
            )
    new_password2 = forms.CharField(max_length=15, min_length=5,
            required=False,
            widget=forms.PasswordInput,
            label=_("New password confirmation"),
            )
    
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError(
                        _("The two password fields didn't match."))
        return password2

    def save(self, commit=True):
        password1 = self.cleaned_data.get('new_password1')
        if password1: 
            self.instance.set_password(password1)
        self.instance.email = self.cleaned_data.get('email')
        self.instance.langue = self.cleaned_data.get('langue')
        if commit:
            self.instance.save()
        return self.instance

    class Meta:
        model = Utilisateur
        fields = ('email', 'langue',)

class CreateLoginsForm(forms.Form):
    """
    Creation de logins à partir d'un fichier csv
    """
    def __init__(self, *args, **kwargs):
        super(CreateLoginsForm, self).__init__(*args, **kwargs)
        self.fields['fermeture'].widget = widgets.AdminSplitDateTime()

    source = forms.FileField(label=_('Source file'))
    groupe = forms.ChoiceField(label=_('Group'))
    langue = forms.ChoiceField(choices=settings.LANGUAGES,
                                label=_('Preferred language'))
    fermeture = forms.DateTimeField(required=False, label=_('Valid till'))
    envoi_mail = forms.ChoiceField(choices=((0,_('No')),(1,_('Yes'))), 
                                label=_('Send credentials by mail'))

