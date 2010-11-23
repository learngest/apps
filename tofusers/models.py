# -*- encoding: utf-8 -*-
"""
Models de l'application tofusers
"""

import datetime

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from email_auth.views import user_logged_in
from toftesting.models import Granule, Question, Reponse

from listes import *

class Client(models.Model):
    """
    Le modèle de base Client.
    
    Définit la référence aux feuilles de style (CSS)
    et un champ libre pour les contacts etc.
    """
    
    nom = models.CharField(max_length=60, unique=True,
        help_text=_("Customer name, required."))
    style = models.CharField(_(u"Custom CSS"),
        max_length=20, null=True, blank=True,
        help_text=_("CSS to use with this customer."))
    contacts = models.TextField(null=True, blank=True,
        help_text=_("Free field (contacts, tel. numbers, ...)."))
    
    class Meta:
        ordering = ['nom']

    def __unicode__(self):
        return self.nom

class SessionTest(models.Model):
    """
    Une session d'examen
    """
    titre = models.CharField(max_length=60, unique=True,
        help_text=_("Session title, required."))
    client = models.ForeignKey(Client, 
        help_text=_("Session customer, required."))
    ouverture = models.DateTimeField(_("Opening date and time."),
        blank=True, null=True,
        help_text=_("Starting the session will not be possible before this date and time."))
    fermeture = models.DateTimeField(_("Closing date and time."),
        blank=True, null=True,
        help_text=_("Starting the session will be possible no later than this date and time."))
    langue = models.CharField(max_length=5, choices=LANGUAGES, 
        default='fr',
        help_text=_(
        "Session language, required."))
    
    class Meta:
        ordering = ['client','ouverture']

    def __unicode__(self):
        return self.titre

class Section(models.Model):
    """
    Une section dans une session de test
    """
    sessiontest = models.ForeignKey(SessionTest,
            help_text=_('Session to which this section belongs, required.'))
    titre = models.CharField(max_length=60, unique=True,
        help_text=_("Section title, required."))
    rang = models.IntegerField(_("rank"))
    
    class Meta:
        ordering = ['sessiontest','rang']

    def __unicode__(self):
        return u'%s - %s' % (self.sessiontest,self.titre)

class Inscrit(models.Model):
    """
    Un user inscrit dans une session d'examen
    """
    sessiontest = models.ForeignKey(SessionTest,
            help_text=_('Session, required.'))
    user = models.ForeignKey(User,
            help_text=_('User, required.'))
    
    class Meta:
        ordering = ['sessiontest','user']

    def __unicode__(self):
        return u'%s - %s' % (self.sessiontest,self.user)

class Contenu(models.Model):
    """
    Classe abstraite pour tous les tests
    """
    section = models.ForeignKey(Section,
            help_text=_('Section, required.'))
    rang = models.IntegerField(_("rank"))
    duree = models.IntegerField(_("Maximum duration, minutes. 0 if unlimited."))

    class Meta:
        abstract = True

class ContenuStd(Contenu):
    """
    Contenu de test standard
    """
    granule = models.ForeignKey(Granule),
        help_text=_('Granule, required.'))
    nbq = models.IntegerField(_("Number of questions"))

    class Meta:
        ordering = ['section','rang']

    def __unicode__(self):
        return u'%s - %s' % (self.section, self.granule)

class ContenuCas(Contenu):
    """
    Contenu : cas à rendre
    """
    titre = models.CharField(max_length=100)
    libel = models.TextField(_("Directions"),
            blank=True, null=True)
    fichier = models.FileField(upload_to='assignments/%Y/%m/%d',
            blank=True,null=True)

    class Meta:
        ordering = ['section','rang']

    def __unicode__(self):
        return u'%s - %s' % (self.section,self.titre)

class ReponseStd(models.Model):
    """
    Réponse à une question standard
    """
    user = models.ForeignKey(User)
    contenu = models.ForeignKey(ContenuStd)
    question = models.ForeignKey(Question)
    reponse = models.ForeignKey(Reponse, blank=True, null=True)
    texte = models.TextField(blank=True, null=True)
    date = models.DateTimeField()

    class Meta:
        pass

    def __unicode__(self):
        return u'%s - %s - %s' % (self.user, self.contenu, self.question)

class ReponseCas(models.Model):
    """
    Devoir rendu par un utilisateur
    """
    user = models.ForeignKey(User)
    cas = models.ForeignKey(ContenuCas)
    date = models.DateTimeField()
    fichier = models.FileField(upload_to=settings.WORKDONE_DIR)
    signature = models.CharField(max_length=54)

    class Meta:
        unique_together = (('utilisateur', 'cas'),)

    def __unicode__(self):
        return u'%s - %s - %s' % (self.utilisateur.email, 
                self.cas.titre, self.date)

