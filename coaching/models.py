# -*- encoding: utf-8 -*-
"""
Models de l'application coaching
"""

import datetime

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, UserManager

from email_auth.views import user_logged_in
from learning.models import Cours, Module
from testing.models import Granule

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
    administrateur = models.ForeignKey('Utilisateur', blank=True, null=True,
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

    cours = models.ManyToManyField(Cours, blank=True, null=True,
        through='CoursDuGroupe',
        help_text=_("Courses to which group members are subscribed."))

    assistant = models.ManyToManyField('Utilisateur', blank=True, null=True,
        through='Assistants', related_name='assistants',
        help_text=_("Group assistants"))

    class Meta:
        ordering = ['client', 'nom']

    def __unicode__(self):
        return "%s - %s" % (self.client.nom, self.nom)

    def save(self, force_insert=False, force_update=False):
        if self.is_demo:
            self.is_open=True
        super(Groupe, self).save()

    def get_admin_url(self):
        from django.core import urlresolvers
        return urlresolvers.reverse('admin:coaching_groupe_change',
                args=(str(self.id),))

    @models.permalink
    def get_absolute_url(self):
        return('coaching.views.groupe', [str(self.id)])

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
        ordering = ['groupe','rang']
        unique_together = (('groupe', 'cours'),)
        verbose_name_plural = _("Groups courses")

    def __unicode__(self):
        return "%s - %s" % (self.groupe, self.cours)

class Assistants(models.Model):
    """
    Assistant pour un groupe
    """

    utilisateur = models.ForeignKey('Utilisateur', related_name='assistant')
    groupe = models.ForeignKey(Groupe)

    class Meta:
        ordering = ('groupe',)
        verbose_name = 'Assistant'
        verbose_name_plural = 'Assistants'

    def __unicode__(self):
        return "%s - %s" % (self.groupe, self.utilisateur)

class Prof(models.Model):
    """
    Professeur pour un groupe-cours
    """

    utilisateur = models.ForeignKey('Utilisateur', related_name='prof')
    groupe = models.ForeignKey(Groupe)
    cours = models.ForeignKey(Cours)

    class Meta:
        ordering = ('groupe',)
        verbose_name = 'Professor'

    def __unicode__(self):
        return "%s - %s - %s" % (self.utilisateur, self.groupe, self.cours)

class Utilisateur(User):
    """
    Utilisateur pour les applications Learngest
    """
    fermeture = models.DateTimeField(_("Expiration date"),
        blank=True, null=True,
        help_text=_("Account is valid till this date. Account is valid forever if empty."))
    langue = models.CharField(max_length=5, choices=settings.LANGUAGES, 
        default='fr',
        help_text=_(
        "User's prefered language for interface, messages and contents, required."))

    statut = models.IntegerField(choices=settings.LISTE_STATUTS, default=0,
        help_text=_("User's status, required."))

    groupe = models.ForeignKey(Groupe, 
        blank=True, null=True, # requis pour la création avec le lien user
        help_text=_("User's group, required and unique."))

    current = models.ForeignKey(Cours,
        verbose_name=_('current course'),
        blank=True, null=True,
        editable=False)
    
    # desérialisation, non éditables
    nb_cours_valides = models.IntegerField(
            _('courses completed'),null=True, editable=False)
    nb_travaux_rendus = models.IntegerField(
            _('assignments uploaded'),null=True, editable=False)
    nb_modules = models.IntegerField(
            _("# modules"), null=True, editable=False)
    # nb modules validés dans le cours courant
    nb_valides = models.IntegerField(
            _("# completed"), null=True, editable=False)
    # nb de cours validés, mais en retard
    nb_retards = models.IntegerField( _("# completed late"),
            null=True, editable=False)
    # nb de retards courant
    nb_actuel = models.IntegerField( _("delays"),
            null=True, editable=False)

    # inutilisé, réservé
    tempspasse = models.IntegerField(blank=True, null=True, editable=False)

    # on conserve le manager de l'objet User
    objects = UserManager()

    class Meta:
        verbose_name = _("User")
        ordering = ('groupe',)

    def __unicode__(self):
        return self.email

    def get_admin_url(self):
        from django.core import urlresolvers
        return urlresolvers.reverse('admin:coaching_utilisateur_change',
                args=(str(self.id),))

    def may_see_groupe(self, grpe):
        """
        True si l'utilisateur peut consulter ce groupe
        """
        if self.is_staff:
            return True
        if grpe.administrateur == self:
            return True
        if self in grpe.assistant.all():
            return True

    @models.permalink
    def get_absolute_url(self):
        return('coaching.views.user', [str(self.id)])

class Event(models.Model):
    """
    Evénements libres à ajouter au calendrier
    Un évènement est rattaché à un groupe
    """
    groupe = models.ForeignKey(Groupe,
            help_text=_("Group, required."))
    date = models.DateTimeField(_("When ?"),
            help_text=_("Event date, required."))
    event = models.CharField(_("Description"),
            help_text=_("Event description, required."), max_length=128)

    class Meta:
        ordering = ['groupe', 'date']
        verbose_name = _("Event")

    def __unicode__(self):
        return "%s - %s" % (self.groupe, self.event)

class CommonResultat(models.Model):
    """
    Classe abstraite pour tous les résultats et validations
    """
    utilisateur = models.ForeignKey(Utilisateur)
    date = models.DateTimeField()

    class Meta:
        abstract = True

class Resultat(CommonResultat):
    """
    Stocke tous les résultats des essais aux tests.
    """
    granule = models.ForeignKey(Granule)
    score = models.IntegerField()

    class Meta:
        ordering = ('-date',)

    def __unicode__(self):
        return u"%s - %s - %s - %d" % (self.utilisateur, 
                        self.granule, self.date, self.score)

    def save(self, force_insert=False, force_update=False):
        if not self.id:
            if not self.date:
                self.date = datetime.datetime.now()
        super(Resultat, self).save(force_insert, force_update)

class GranuleValide(CommonResultat):
    """
    Stocke les granules validées pour un utilisateur.
    """
    granule = models.ForeignKey(Granule)
    score = models.IntegerField()

    class Meta:
        unique_together = (('utilisateur','granule'),)

    def __unicode__(self):
        return u"%s - %s - %s - %d" % (self.utilisateur, 
                            self.granule, self.date, self.score)

    def save(self, force_insert=False, force_update=False):
        if not self.id:
            if not self.date:
                self.date = datetime.datetime.now()
        super(GranuleValide, self).save(force_insert, force_update)

class ModuleValide(CommonResultat):
    """
    Stocke les modules validés pour un utilisateur.
    """
    module = models.ForeignKey(Module)

    class Meta:
        unique_together = (('utilisateur','module'),)

    def __unicode__(self):
        return u"%s - %s - %s" % (self.utilisateur,
                        self.module, self.date)

    def save(self, force_insert=False, force_update=False):
        if not self.id:
            if not self.date:
                self.date = datetime.datetime.now()
        super(ModuleValide, self).save(force_insert, force_update)

class CoursValide(CommonResultat):
    """
    Stocke les cours validés pour un utilisateur.
    """
    cours = models.ForeignKey(Cours)

    class Meta:
        unique_together = (('utilisateur','cours'),)

    def __unicode__(self):
        return u"%s - %s - %s" % (self.utilisateur, self.cours, self.date)

    def save(self, force_insert=False, force_update=False):
        if not self.id:
            if not self.date:
                self.date = datetime.datetime.now()
        super(CoursValide, self).save(force_insert, force_update)

def upload_path(instance, filename):
    import os.path
    from django.template.defaultfilters import slugify
    return os.path.join('otherdocs',
                slugify(instance.groupe.nom),
                instance.cours.slug,
                filename)

class AutresDocs(models.Model):
    """
    Documents supplémentaires pour un groupes-cours
    """

    groupe = models.ForeignKey(Groupe)
    cours = models.ForeignKey(Cours)
    titre = models.CharField(max_length=100)
    fichier = models.FileField(upload_to=upload_path)

    class Meta:
        ordering = ['groupe','cours']
        verbose_name = _("Additional document")
        verbose_name_plural = _("Additional documents")

    def __unicode__(self):
        return u'%s - %s - %s' % (self.titre, self.groupe, self.cours)

    def get_absolute_url(self):
        return self.fichier.url

class Work(models.Model):
    """
    Devoir à rendre par un groupe pour un cours.
    """

    groupe = models.ForeignKey(Groupe)
    cours = models.ForeignKey(Cours)
    titre = models.CharField(max_length=100)
    libel = models.TextField(_("Directions"),
            blank=True, null=True)
    fichier = models.FileField(upload_to='assignments/%Y/%m/%d',
            blank=True,null=True)

    class Meta:
        ordering = ['groupe','cours']
        verbose_name = _("Assignment")
        verbose_name_plural = _("Assignments")

    def __unicode__(self):
        return u'%s - %s - %s' % (self.titre, self.groupe, self.cours)

    @models.permalink
    def get_absolute_url(self):
        return('learning.views.assignment', [str(self.id)])

class WorkDone(models.Model):
    """
    Devoir rendu par un utilisateur
    """

    utilisateur = models.ForeignKey(Utilisateur)
    work = models.ForeignKey(Work)
    date = models.DateTimeField()
    fichier = models.FileField(upload_to=settings.WORKDONE_DIR)
    signature = models.CharField(max_length=54)

    class Meta:
        unique_together = (('utilisateur', 'work'),)

    def __unicode__(self):
        return u'%s - %s - %s' % (self.utilisateur.login, 
                self.work.titre, self.date)

