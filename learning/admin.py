# -*- encoding: utf-8 -*-
# vim:encoding=utf-8:ft=python.django

from django.contrib import admin
from learning.models import Module, ModuleTitre, Cours, CoursTitre, ModuleCours, Contenu

class ModuleAdmin(admin.ModelAdmin):
    ordering = ['slug'] 
admin.site.register(Module, ModuleAdmin)

class ModuleTitreAdmin(admin.ModelAdmin):
    list_filter = ('langue',)
    list_display = ('module','langue','titre')
    list_per_page = 30
    ordering = ['module'] 
admin.site.register(ModuleTitre, ModuleTitreAdmin)

class CoursAdmin(admin.ModelAdmin):
    ordering = ['rang'] 
admin.site.register(Cours, CoursAdmin)

class CoursTitreAdmin(admin.ModelAdmin):
    list_filter = ('langue',)
    list_display = ('cours','langue','titre')
    list_per_page = 30
    ordering = ['cours'] 
admin.site.register(CoursTitre, CoursTitreAdmin)

class ModuleCoursAdmin(admin.ModelAdmin):
    list_filter = ('cours',)
    list_display = ('cours','module','rang',)
    ordering = ['cours','rang']
admin.site.register(ModuleCours, ModuleCoursAdmin)

class ContenuAdmin(admin.ModelAdmin):
        list_filter = ('langue','type')
        list_display = ('module','ressource','type','langue','titre')
        list_per_page = 30
        search_fields = ('titre',)
        ordering = ['module'] 
admin.site.register(Contenu, ContenuAdmin)


