# -*- encoding: utf-8 -*-

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from django import forms
from django.forms import ModelForm

from coaching.models import Client, Groupe, Utilisateur, CoursDuGroupe, Event, Work

admin.site.unregister(User)
admin.site.unregister(Group)

class ClientAdmin(admin.ModelAdmin):
    search_fields = ('nom',)
admin.site.register(Client, ClientAdmin)

class CoursDuGroupeInline(admin.TabularInline):
    model = CoursDuGroupe
    verbose_name_plural = _('Group courses')

class GroupeAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('nom',)}),
        (None, {'fields': ('administrateur','client')}),
        ('Permissions', {'fields': ('is_demo', 'is_open')}),
    )
    list_display = ('client','nom','administrateur','is_demo','is_open')
    list_display_links = ('nom',)
    list_filter = ('client',)
    search_fields = ('nom',)
    inlines = (CoursDuGroupeInline,)
admin.site.register(Groupe, GroupeAdmin)

class WorkAdmin(admin.ModelAdmin):
    fieldsets = (
            (None, {'fields': ('groupe','cours',)}),
            (None, {'fields': ('titre','fichier','libel',)}),
    )
    list_display = ('groupe','cours','titre',)
    list_display_links = ('titre',)
    list_filter = ('groupe','cours',)
admin.site.register(Work, WorkAdmin)

class CoursDuGroupeAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('groupe', 'cours', 'rang')}),
        ('Dates', {'fields': ('debut', 'fin')}),
    )
    list_display = ('groupe','cours', 'rang', 'debut', 'fin',)
    list_display_links = ('cours',)
    list_filter = ('groupe',)
    list_editable = ('rang','debut','fin',)
#admin.site.register(CoursDuGroupe, CoursDuGroupeAdmin)

class UtilisateurAdminForm(ModelForm):
    username = forms.EmailField(label=_("Username"), max_length=75)
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput,
            required=False)
    password2 = forms.CharField(label=_("Password confirmation"), 
            widget=forms.PasswordInput, required=False)

    class Meta:
        model = Utilisateur
        exclude = ('password', 'email')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2

    def save(self, commit=True):
        user = super(UtilisateurAdminForm, self).save(commit=False)
        user.email = user.username
        if self.cleaned_data["password1"]:
            user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UtilisateurCreationForm(ModelForm):
    username = forms.EmailField(label=_("Username"), max_length=75)
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput)

    class Meta:
        model = Utilisateur
        fields = ("username",)

    def clean_username(self):
        username = self.cleaned_data["username"].lower()
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
        user.email = user.username
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UtilisateurAdmin(UserAdmin):
    form = UtilisateurAdminForm
    add_form = UtilisateurCreationForm
    fieldsets = (
        (None, {'fields': ('username', 'password1', 'password2')}),
        (_("Identity"), 
                {'fields': ('last_name', 'first_name')}),
        (_("Parameters"), {'fields': ('statut', 'langue', 'groupe', 'fermeture')}),
        (_('Permissions'), {'fields': ('is_staff', 'is_active', 'is_superuser', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Groups'), {'fields': ('groups',)}),
    )
    list_display = ('groupe', 'email', 'last_name', 'first_name')
    list_display_links = ('email',)
    list_filter = ('groupe', 'langue', 'fermeture')
    search_fields = ('email', 'last_name',)
admin.site.register(Utilisateur, UtilisateurAdmin)

class EventAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('groupe', 'date', 'event')}),
    )
    list_display = ('groupe','date','event')
    list_display_links = ('groupe',)
    list_editable = ('date','event')
admin.site.register(Event, EventAdmin)
