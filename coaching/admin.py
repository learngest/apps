# -*- encoding: utf-8 -*-
# vim:encoding=utf-8:

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.admin import UserAdmin
from django import forms
from django.forms import ModelForm

from coaching.models import Client, Groupe, Utilisateur

class ClientAdmin(admin.ModelAdmin):
    search_fields = ('nom',)
    
admin.site.register(Client, ClientAdmin)

class GroupeAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('nom',)}),
        (None, {'fields': ('administrateur','client')}),
        ('Cours', {'fields': ('cours',)}),
        ('Permissions', {'fields': ('is_demo', 'is_open')}),
    )
    list_display = ('client','nom','administrateur','is_demo','is_open')
    list_display_links = ('nom',)
    list_filter = ('client',)
    search_fields = ('nom',)
    filter_horizontal = ('cours',)

admin.site.register(Groupe, GroupeAdmin)

class UtilisateurAdminForm(ModelForm):
    class Meta:
        model = Utilisateur

class UtilisateurCreationForm(ModelForm):
    username = forms.RegexField(label=_("Username"), max_length=30, regex=r'^\w+$',
        help_text = _("Required. 30 characters or fewer. Alphanumeric characters only (letters, digits and underscores)."),
        error_message = _("This value must contain only letters, numbers and underscores."))
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput)

    class Meta:
        model = Utilisateur
        fields = ("username",)

    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            Utilisateur.objects.get(username=username)
        except Utilisateur.DoesNotExist:
            return username
        raise forms.ValidationError(_("A user with that username already exists."))

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2

    def save(self, commit=True):
        user = super(UtilisateurCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UtilisateurAdmin(UserAdmin):
    form = UtilisateurAdminForm
    add_form = UtilisateurCreationForm
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_(u"Informations personnelles"), 
                {'fields': ('last_name', 'first_name', 'email')}),
        (_(u"Paramètres"), {'fields': ('langue', 'groupe', 'fermeture')}),
    )
    list_display = ('groupe', 'username', 'last_name', 'first_name')
    list_display_links = ('username',)
    list_filter = ('groupe', 'langue', 'fermeture')
    search_fields = ('username', 'last_name',)

admin.site.register(Utilisateur, UtilisateurAdmin)
