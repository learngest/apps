# -*- encoding: utf-8 -*-
# vim:encoding=utf-8:ft=python.django
"""
Models de l'application coaching
"""

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, UserManager

from email_auth.views import user_logged_in
from learning.models import Cours

def set_language(sender, **kwargs):
    """
    Récup le signal user_logged_in envoyé par email_auth
    Place la langue favorite du user dans la session
    """
    if hasattr(sender,'langue') and sender.langue:
        kwargs['request'].session['django_language'] = sender.langue

user_logged_in.connect(set_language)

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

class Groupe(models.Model):
    """
    Le modèle de base groupe (Groupe).

    Un groupe appartient à un Client (institution).
    Un groupe possède au plus un administrateur qui est un User.
    L'administrateur peut avoir plusieurs groupes et peut gérer ses
    groupes (passer un étudiant d'un groupe à l'autre p. ex.)
    Un Utilisateur appartient à un et un seul groupe et hérite de
    ses cours.
    Drapeaux :
    - is_demo : les Utilisateurs du groupe ne peuvent pas faire de tests
    - is_open : les Utilisateurs du groupe peuvent consulter tous les cours, 
      indépendamment de leurs résultats aux tests.
    Un groupe is_demo est forcément is_open.
    """

    nom = models.CharField(max_length=60, unique=True,
        help_text=_("Group name, required."))
    administrateur = models.ForeignKey(User, blank=True, null=True, 
        related_name='groupes',
        help_text=_("Group admin (an admin User)."))
    client = models.ForeignKey(Client, 
        help_text=_("Group customer, required."))

    is_demo = models.BooleanField(_("Demo group"),
        default=False,
        help_text=_("If True, this group is not allowed to take tests, and all courses are open."))
    is_open = models.BooleanField(_("Open courses"),
        default=False,
        help_text=_("If True, all courses are open, whatever the tests results."))

#    cours = models.ManyToManyField(Cours, blank=True, null=True,
#        help_text=_("Courses to which group members are subscribed."))

    class Meta:
        ordering = ['client', 'nom']

    def __unicode__(self):
        return "%s - %s" % (self.client.nom, self.nom)

    def save(self, force_insert=False, force_update=False):
        if self.is_demo:
            self.is_open=True
        super(Groupe, self).save()

class CoursDuGroupe(models.Model):
    """
    Les cours associés à un groupe.
    Les cours sont ordonnés sur le rang.
    Un cours peut avoir :
    - une date d'ouverture au plus tôt
    - une date de validation au plus tard
    """
    groupe = models.ForeignKey(Groupe,
            help_text=_("Group, required."))
    cours = models.ForeignKey(Cours,
            help_text=_("Course, required."))
    rang = models.IntegerField(_("rank"))
    debut = models.DateTimeField(_("Opening date"),
            blank=True, null=True,
            help_text=_("Date at which the course will open"))
    fin = models.DateTimeField(_("Deadline"),
            blank=True, null=True,
            help_text=_("Course deadline"))

    class Meta:
        ordering = ['groupe', 'rang']
        unique_together = (('groupe', 'cours'),)
        verbose_name_plural = _("Groups courses")

    def __unicode__(self):
        return "%s - %s" % (self.groupe, self.cours)

class Utilisateur(User):
    """
    Utilisateur pour les applications Learngest
    """
    fermeture = models.DateTimeField(_("Expiration date"),
        blank=True, null=True,
        help_text=_("Account is valid till this date. Account is valid forever if empty."))
    langue = models.CharField(max_length=5, choices=settings.LISTE_LANGUES, 
        default='fr',
        help_text=_(
        "User's prefered language for interface, messages and contents, required."))
    groupe = models.ForeignKey(Groupe, 
        blank=True, null=True, # requis pour la création avec le lien user
        help_text=_("User's group, required and unique."))

    
    # desérialisation, non éditables
    nb_modules = models.IntegerField(
            _("# modules"),
            default=0, editable=False)
    nb_valides = models.IntegerField(
            _("# completed"),
            default=0, editable=False)
    # nb de modules validés, mais en retard
    nb_retards = models.IntegerField(
            _("# completed late"),
            default=0, editable=False)
    # nb de retards courant
    nb_actuel = models.IntegerField(
            _("# currently late"),
            default=0, editable=False)

    # inutilisé, réservé
    tempspasse = models.IntegerField(blank=True, null=True, editable=False)

    class Meta:
        verbose_name = _("User")
        ordering = ('groupe',)

    # on conserve le manager de l'objet User
    objects = UserManager()

class Event(models.Model):
    """
    Evénements libres à ajouter au calendrier
    Un évènement est rattaché à un groupe
    """
    groupe = models.ForeignKey(Groupe,
            help_text=_("Group, required."))
    date = models.DateTimeField(_("Event date, required."))
    event = models.CharField(_("Event description, required."), max_length=128)
