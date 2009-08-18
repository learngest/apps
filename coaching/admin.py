# -*- encoding: utf-8 -*-
# vim:encoding=utf-8:

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

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

class UtilisateurAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_(u"Informations personnelles"), 
                {'fields': ('first_name', 'last_name', 'email')}),
        (_(u"Paramètres"), {'fields': ('langue', 'groupe', 'fermeture')}),
    )
    list_display = ('groupe', 'username', 'last_name', 'first_name')
    list_display_link = ('username')
    list_filter = ('groupe', 'langue', 'fermeture')
    search_fields = ('username', 'last_name',)
admin.site.register(Utilisateur, UtilisateurAdmin)
