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

class WorkForm(forms.Form):
    """
    Affichage et rendu de devoirs
    """
    fichier = forms.FileField(required=False,label=_('File name'))

    def clean_fichier(self):
        if self.cleaned_data['fichier']:
            fichier_ok = False
            # le test devrait se faire sur le content-type
            for suffix in ('.doc','.docx','.pdf','.xls','.xlsx','.zip'):
                if self.cleaned_data['fichier'].name.endswith(suffix):
                    fichier_ok = True
                    break
            if not fichier_ok:
                raise forms.ValidationError(
                    _('Filetype should be .doc, .docx, .xls, .xslx, .pdf or .zip'))
            filelen = float(self.cleaned_data['fichier'].size) / 1024
            if filelen > 1024:
                filelen = filelen / 1024
                raise forms.ValidationError(
                    _('Maximum size allowed is 1 Mo, this file is %.2f Mo' % filelen))
        return self.cleaned_data['fichier']

class MailForm(forms.Form):
    """
    Formulaire d'envoi de mails
    """
    subject = forms.CharField(max_length=100, label=_('Subject'))
    content = forms.CharField(widget=forms.Textarea,label=_('Text'),required=False)
    attach = forms.FileField(widget=forms.FileInput,
            label=_('Attach a file'), required=False)

    def clean_attach(self):
        if self.cleaned_data['attach']:
            filelen = float(self.cleaned_data['attach'],size) / 1024
            if filelen > 1024:
                raise forms.ValidationError(
                    _('Maximum size allowed is 1 Mo, this file is %.2f Mo' % filelen))
        return self.cleaned_data['attach']
