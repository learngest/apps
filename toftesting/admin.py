# -*- encoding: utf-8 -*-

from django.contrib import admin
from testing.models import Granule, GranuleTitre, Enonce, Question, Reponse

class GranuleAdmin(admin.ModelAdmin):
    ordering = ['slug'] 
    list_display = ('id','slug',)
    list_display_links = ('slug',)
admin.site.register(Granule, GranuleAdmin)

class GranuleTitreAdmin(admin.ModelAdmin):
    list_filter = ('langue',)
    list_display = ('granule','langue','titre')
    list_per_page = 30
    ordering = ['granule'] 
admin.site.register(GranuleTitre, GranuleTitreAdmin)

class EnonceAdmin(admin.ModelAdmin):
    search_fields = ['libel']
    list_display = ('id','libel')
admin.site.register(Enonce, EnonceAdmin)

class QuestionAdmin(admin.ModelAdmin):
    search_fields = ['libel']
    list_display = ('id','libel')
    list_filter = ('langue','granule')
admin.site.register(Question, QuestionAdmin)

class ReponseAdmin(admin.ModelAdmin):
    list_display = ('id','question','points','valeur')
admin.site.register(Reponse, ReponseAdmin)

