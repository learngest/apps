# -*- encoding: utf-8 -*-

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

class Module(models.Model):
    """
    Le modèle de base Module.

    Les cours sont composés de plusieurs modules.
    Un module peut appartenir à plusieurs cours.
    Les modules sont ordonnés dans le cours, voir ModuleCours.

    Un module est formé de ressources (Contenu) dans différentes langues.
    Un module possède des tests dans différentes langues.
    """
    slug = models.SlugField(unique=True, db_index=True)

    class Meta:
        ordering = ['slug'] 

    def __unicode__(self):
        return self.slug

    def titre(self, langue):
        try:
            mt = self.moduletitre_set.get(langue=langue).titre
        except ModuleTitre.DoesNotExist:
            mt = self.slug
        return mt

    def rang(self, cours):
        """
        Renvoie le rang de ce module dans le cours.
        """
        try:
            mc = ModuleCours.objects.get(module=self, cours=cours)
        except ModuleCours.DoesNotExist:
            return 0
        return mc.rang

class ModuleTitre(models.Model):
    """
    Titre d'un module dans la langue choisie
    """
    module = models.ForeignKey(Module)
    langue = models.CharField(max_length=5, choices=settings.LISTE_LANGUES)
    titre = models.CharField(max_length=100)

    class Meta:
        ordering = ['module'] 
        verbose_name = _("module title")

    def __unicode__(self):
        return '%s : %s' % (self.module, self.titre)

class Cours(models.Model):
    """
    Le modèle de base Cours.

    Les cours sont composés de plusieurs modules.
    Un module peut appartenir à plusieurs cours.
    Les modules sont ordonnés dans le cours, voir ModuleCours.
    Les cours sont également ordonnés.
    """
    slug = models.SlugField(unique=True, db_index=True)
#    rang = models.IntegerField()

    class Meta:
        verbose_name = _("course")
        ordering = ['slug']

    def __unicode__(self):
        return self.slug

    def titre(self, langue):
        try:
            ct = self.courstitre_set.get(langue=langue).titre
        except CoursTitre.DoesNotExist:
            ct = self.slug
        return ct

class CoursTitre(models.Model):
    """
    Titre d'un cours dans la langue choisie
    """
    cours = models.ForeignKey(Cours)
    langue = models.CharField(max_length=5, choices=settings.LISTE_LANGUES)
    titre = models.CharField(max_length=100)

    class Meta:
        verbose_name = _("course title")
        ordering = ['cours'] 

    def __unicode__(self):
        return '%s : %s' % (self.cours, self.titre)

class ModuleCours(models.Model):
    """
    Un module dans un cours avec un certain rang.
    Voir django_src/tests/modeltests/m2m_intermediary

    Les cours sont composés de plusieurs modules.
    Un module peut appartenir à plusieurs cours.
    Les modules sont ordonnés dans le cours, voir ModuleCours.
    """
    cours = models.ForeignKey(Cours)
    module = models.ForeignKey(Module)
    rang = models.IntegerField()

    class Meta:
        ordering = ['cours','rang']
        verbose_name = _(u"course modules")

    def __unicode__(self):
        return u'%s - %s - %s' % (self.cours.slug, self.module.slug, self.rang)

class Contenu(models.Model):
    """
    Le modèle de base Contenu.

    Les cours sont composés de plusieurs modules.
    Un module peut appartenir à plusieurs cours.
    Les modules sont formés de Contenus dans différentes langues.
    """
    ressource = models.CharField(max_length=50)
    langue = models.CharField(max_length=5, choices=settings.LISTE_LANGUES)
    type = models.CharField(max_length=3, choices=settings.LISTE_TYPES, 
            default='htm')
    titre = models.CharField(max_length=100)
    module = models.ForeignKey(Module)

    class Meta:
        ordering = ['module'] 

    def __unicode__(self):
        return '%s (%s)' % (self.titre, self.ressource)

