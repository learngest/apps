# -*- encoding: utf-8 -*-

from django.contrib import admin
from django import forms
from django.forms import ModelForm, Textarea
from apps.testing.models import Granule, GranuleTitre, Enonce, Question, Reponse
from apps.testing.models import Examen, ExamCas, ExamEnonce, ExamQuestion, ExamReponse

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
    search_fields = ['libel','id']
    list_display = ('id','libel')
admin.site.register(Enonce, EnonceAdmin)

class QuestionAdmin(admin.ModelAdmin):
    search_fields = ['libel','enonce__libel','id','enonce__id',]
    list_display = ('enonce_id','id','libel')
    list_display_links = ('id',)
    list_filter = ('langue','granule')
    fieldsets = (
        (None, {'fields': ('enonce',)}),
        ('Question', {'fields': ('granule', 'langue', 'typq', 'libel',)}),
    )
    readonly_fields = ('enonce',)

    def enonce_id(self, obj):
        return "<a href=\"%s\">%s</a>" % (
                obj.enonce.get_admin_url(), obj.enonce.id)
    enonce_id.short_description = 'ID enonce'
    enonce_id.admin_order_field = 'enonce'
    enonce_id.allow_tags = True

admin.site.register(Question, QuestionAdmin)

class ReponseForm(forms.ModelForm):
    enonce = forms.CharField(required=False)

    class Meta:
        model = Reponse
        widgets = {'valeur': Textarea(attrs={'cols': 80, 'rows': 2}),}

class ReponseAdmin(admin.ModelAdmin):
    form = ReponseForm
    search_fields = ['valeur','question__libel','question__id',
                    'question__enonce__libel']
    list_display = ('enonce_id','question_id','id','valeur','points')
    list_display_links = ('id',)
    fieldsets = (
        (None, {'fields': ('enonce','question',)}),
        ('Réponse', {'fields': ('points', 'valeur')}),
    )
    readonly_fields = ('enonce', 'question',)

    def question_id(self, obj):
        return "<a href=\"%s\">%s</a>" % (
                obj.question.get_admin_url(), obj.question.id)
    question_id.short_description = 'ID question'
    question_id.admin_order_field = 'question'
    question_id.allow_tags = True

    def enonce_id(self, obj):
        return "<a href=\"%s\">%s</a>" % (
                obj.question.enonce.get_admin_url(), obj.question.enonce.id)
    enonce_id.short_description = 'ID enonce'
    enonce_id.admin_order_field = 'enonce'
    enonce_id.allow_tags = True

admin.site.register(Reponse, ReponseAdmin)

class ExamCasAdmin(admin.ModelAdmin):
    list_display = ('id','slug','examen','ressource')
    list_display_links = ('slug',)
    list_per_page = 30
    search_fields = ('titre', 'slug',)
    ordering = ['examen','slug']
admin.site.register(ExamCas, ExamCasAdmin)

class ExamEnonceAdmin(admin.ModelAdmin):
    search_fields = ['libel']
    list_display = ('id','libel')
admin.site.register(ExamEnonce, ExamEnonceAdmin)

class ExamQuestionAdmin(admin.ModelAdmin):
    search_fields = ['libel']
    list_display = ('id','libel')
    list_filter = ('langue','examen')
admin.site.register(ExamQuestion, ExamQuestionAdmin)

class ExamReponseAdmin(admin.ModelAdmin):
    list_display = ('id','question','points','valeur')
admin.site.register(ExamReponse, ExamReponseAdmin)

class ExamenAdmin(admin.ModelAdmin):
    fieldsets = (
            (None, {'fields': ('groupe','cours',)}),
            (None, {'fields': ('titre','debut','fin','display_note')}),
    )
    list_display = ('groupe','cours','titre','debut','fin','display_note',)
    list_display_links = ('titre',)
    list_filter = ('groupe','cours',)
admin.site.register(Examen, ExamenAdmin)
