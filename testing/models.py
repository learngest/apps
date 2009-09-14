# -*- encoding: utf-8 -*-

from django.db import models
from django.conf import settings

from learning.models import Module

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

class GranuleTitre(models.Model):
    """
    Titre d'une granule dans la langue choisie
    """
    granule = models.ForeignKey(Granule)
    langue = models.CharField(max_length=5, choices=settings.LISTE_LANGUES)
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
    langue = models.CharField(max_length=5, choices=settings.LISTE_LANGUES)
    typq = models.CharField(max_length=3, 
            choices=settings.LISTE_TYPQ, default='exa')
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
