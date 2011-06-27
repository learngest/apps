# -*- encoding: utf-8 -*-

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from learning.models import Module, Cours

from listes import *

class Granule(models.Model):
    """
    Une granule de test.
    Un module peut avoir une ou plusieurs granules de tests.
    """
    slug = models.SlugField()
    module = models.ForeignKey(Module)
    nbq = models.IntegerField()
    score_min = models.IntegerField()
    rang = models.IntegerField()

    class Meta:
        ordering = ['module','rang']

    def __unicode__(self):
        return self.slug

    def titre(self, langue):
        try:
            gt = self.granuletitre_set.get(langue=langue).titre
        except GranuleTitre.DoesNotExist:
            gt = self.slug
        return gt

    @models.permalink
    def get_absolute_url(self):
        return('testing.views.test', [str(self.id)])

class GranuleTitre(models.Model):
    """
    Titre d'une granule dans la langue choisie
    """
    granule = models.ForeignKey(Granule)
    langue = models.CharField(max_length=5, choices=LANGUAGES)
    titre = models.CharField(max_length=100)

    class Meta:
        #ordering = ['granule',] 
        pass

    def __unicode__(self):
        return '%s : %s' % (self.granule, self.titre)

class Enonce(models.Model):
    """
    Un énoncé pour un ensemble de questions.
    """
    libel = models.TextField() 

    def __unicode__(self):
        return self.libel

class Question(models.Model):
    """
    Le modèle de base Question.

    Une question a un énoncé (Enonce).
    Une question se rattache à une granule.
    Elle est formulée dans une langue.
    """
    enonce = models.ForeignKey(Enonce)
    granule = models.ForeignKey(Granule)
    langue = models.CharField(max_length=5, choices=LANGUAGES)
    typq = models.CharField(max_length=3, 
            choices=LISTE_TYPQ, default='exa')
    libel = models.TextField() 

    def __unicode__(self):
        return self.libel

class Reponse(models.Model):
    """
    Le modèle de base Reponse.
    Il y a une réponse par question sauf pour les QCM et les QRM.
    """
    question = models.ForeignKey(Question)
    points = models.IntegerField()
    valeur = models.CharField(max_length=255)

    def __unicode__(self):
        return self.valeur

class Examen(models.Model):
    """
    Modèle des examens
    Rattaché à un cours ou à rien du tout
    """
    groupe = models.ForeignKey('coaching.Groupe')
    cours = models.ForeignKey(Cours, blank=True, null=True)
    titre = models.CharField(max_length=100)
    debut = models.DateTimeField(blank=True, null=True)
    fin = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['groupe','cours']

    def __unicode__(self):
        return self.titre

    def get_results_url(self):
        from django.core import urlresolvers
        return urlresolvers.reverse('coaching.views.examresults',
                args=(str(self.id),))

class ExamCas(models.Model):
    """
    Texte d'un cas d'examen
    """
    examen = models.ForeignKey(Examen)
    titre = models.CharField(max_length=100)
    slug = models.SlugField()
    ressource = models.CharField(max_length=50)

    class Meta:
        ordering = ['examen']
        verbose_name = _("Case study for exams")
        verbose_name_plural = _("Case studies for exams")

    def __unicode__(self):
        return self.titre

    @models.permalink
    def get_absolute_url(self):
        return('testing.views.cas', [str(self.id)])

class ExamEnonce(models.Model):
    """
    Un énoncé pour un ensemble de questions dans un examen.
    """
    libel = models.TextField() 

    class Meta:
        verbose_name = _("Case study question text")
        verbose_name_plural = _("Case study question texts")

    def __unicode__(self):
        return self.libel

class ExamQuestion(models.Model):
    """
    Le modèle de base Question.

    Une question a un énoncé (Enonce).
    Une question se rattache à un cas.
    Elle est formulée dans une langue.
    """
    enonce = models.ForeignKey(ExamEnonce)
    examen = models.ForeignKey(ExamCas)
    langue = models.CharField(max_length=5, choices=LANGUAGES)
    typq = models.CharField(max_length=3, 
            choices=LISTE_TYPQ, default='exa')
    libel = models.TextField() 

    class Meta:
        ordering = ['examen']
        verbose_name = _("Case study question")
        verbose_name_plural = _("Case study questions")

    def __unicode__(self):
        return self.libel

class ExamReponse(models.Model):
    """
    Le modèle de base Reponse.
    Il y a une réponse par question sauf pour les QCM et les QRM.
    """
    question = models.ForeignKey(ExamQuestion)
    points = models.IntegerField()
    valeur = models.CharField(max_length=255)

    class Meta:
        ordering = ['question']
        verbose_name = _("Case study question answer")
        verbose_name_plural = _("Case study question answers")

    def __unicode__(self):
        return self.valeur

