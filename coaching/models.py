# -*- encoding: utf-8 -*-
# vim:encoding=utf-8:ft=python.django
"""
Models de l'application coaching
"""

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, UserManager

from django_email_auth.views import user_logged_in
from learning.models import Cours

def set_language(sender, **kwargs):
    """
    Récup le signal user_logged_in envoyé par django_email_auth
    Place la langue favorite du user dans la session
    """
    if sender.langue:
        kwargs['request'].session['django_language'] = sender.langue

user_logged_in.connect(set_language)

class Client(models.Model):
    """
    Le modèle de base Client.
    
    Définit la référence aux feuilles de style (CSS)
    et un champ libre pour les contacts etc.
    """
    
    nom = models.CharField(max_length=60, unique=True,
        help_text=_(u"Nom du client, requis."))
    style = models.CharField(_(u"feuille de style spécifique"),
        max_length=20, null=True, blank=True,
        help_text=_(u"Feuille de style à utiliser, facultatif."))
    contacts = models.TextField(null=True, blank=True,
        help_text=_(u"Champ libre (contacts, téléphones, etc.), facultatif."))
    
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
    Un groupe est inscrit à zéro, un ou plusieurs cours.
    """

    nom = models.CharField(max_length=60, unique=True,
        help_text=_(u"Nom du groupe, requis."))
    administrateur = models.ForeignKey(User, blank=True, null=True, 
        related_name='groupes',
        help_text=_(u"Utilisateur administrateur de ce groupe, facultatif."))
    client = models.ForeignKey(Client, 
        help_text=_(u"Client auquel appartient ce groupe, requis."))

    is_demo = models.BooleanField(_(u"groupe de démonstration"),
        default=False,
        help_text=_(u"Si vrai, ce groupe n'a pas accès aux tests, et tous ses cours lui sont ouverts."))
    is_open = models.BooleanField(_(u"cours ouverts par défaut"),
        default=False,
        help_text=_(u"Si vrai, tous les cours sont ouverts indépendamment des résultats aux tests."))

    cours = models.ManyToManyField(Cours, blank=True, null=True,
        help_text=_(u"Liste des cours auxquels les membres du groupe sont inscrits."))

    class Meta:
        ordering = ['client', 'nom']

    def __unicode__(self):
        return "%s - %s" % (self.client.nom, self.nom)

    def save(self, force_insert=False, force_update=False):
        if self.is_demo:
            self.is_open=True
        super(Groupe, self).save()

class Utilisateur(User):
    """
    Utilisateur pour les applications Learngest
    """
    fermeture = models.DateTimeField(_(u"validité"),
        blank=True, null=True,
        help_text=_(u"Date jusqu'à laquelle le compte de cet utilisateur est valide. Laisser vide pour validité permanente."))
    langue = models.CharField(max_length=5, choices=settings.LISTE_LANGUES, 
        default='fr',
        help_text=_(u"Langue préférée pour l'affichage des messages et contenus"))
    groupe = models.ForeignKey(Groupe, 
        blank=True, null=True, # requis pour la création avec le lien user
        help_text=_(u"Groupe unique auquel appartient cet utilisateur"))

    
    # desérialisation, non éditables
    nb_modules = models.IntegerField(
            _(u"Total modules"),
            default=0, editable=False)
    nb_valides = models.IntegerField(
            _(u"validés"),
            default=0, editable=False)
    # nb de modules validés, mais en retard
    nb_retards = models.IntegerField(
            _(u"validés en retard"),
            default=0, editable=False)
    # nb de retards courant
    nb_actuel = models.IntegerField(
            _(u"retards courants"),
            default=0, editable=False)

    # inutilisé, réservé
    tempspasse = models.IntegerField(blank=True, null=True, editable=False)

    class Meta:
        verbose_name = _("utilisateur")
        ordering = ('groupe',)

    # on conserve le manager de l'objet User
    objects = UserManager()
