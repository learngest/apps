# -*- encoding: utf-8 -*-

import datetime

from django.utils.translation import ugettext as _
from django.core.cache import cache

from coaching.models import CoursDuGroupe
from learning.models import Contenu
from testing.models import Granule
from testing.controllers import UserGranule

def user_may_see(user, contenu):
    """
    Renvoie True si l'utilisateur peut voir le contenu :
    le contenu appartient à un cours ouvert du groupe de l'Utilisateur
    """
    modules_key = "Utilisateur.%s.liste_modules_autorises" % user.id
    liste_modules_autorises = cache.get(modules_key)
    if not liste_modules_autorises:
        cours_key = "Utilisateur.%s.liste_cours_ouverts" % user.id
        liste_cours_ouverts = cache.get(cours_key)
        if not liste_cours_ouverts:
            cdgs = CoursDuGroupe.objects.filter(groupe=user.groupe)
            ucs = [UserCours(user, cdg.cours) for cdg in cdgs]
            liste_cours_ouverts = [uc.cours for uc in ucs if uc.is_open()]
            cache.set(cours_key, liste_cours_ouverts)
        liste_modules_autorises = [m for cours in liste_cours_ouverts
                            for m in cours.liste_modules()]
        cache.set(modules_key, liste_modules_autorises)
    return contenu.module in liste_modules_autorises

class UserModule(object):
    """
    Controller d'un module pour un utilisateur
    """
    def __init__(self, user, module):
        self.user = user
        self.module = module
        self.titre = self.module.titre(self.user.langue)
        self.contents = Contenu.objects.filter(module=self.module,
                langue=self.user.langue)
        self.tests = [UserGranule(self.user,g)
                for g in Granule.objects.filter(module=self.module)]

    def date_validation(self):
        """
        Renvoie la date de validation du module
        False s'il n'est pas validé
        None si le module n'a pas de tests
        """
        dates =  [t.date_validation() for t in self.tests]
        if not dates:
            return None
        if False in dates:
            return False
        else:
            return max(dates)

    def cours(self):
        """
        Renvoie l'objet Cours auquel appartient le module pour
        cet utilisateur
        """
        liste_cours = self.user.groupe.liste_cours()
        for c in liste_cours:
            if self.module in [mc.module for mc in c.modulecours_set.all()]:
                return c
        return None

class UserCours(object):
    """
    Controller d'un cours pour un utilisateur
    """
    def __init__(self, user, cours):
        self.user = user
        self.cours = cours
        cdg = CoursDuGroupe.objects.get(cours=self.cours,groupe=self.user.groupe)
        self.debut = cdg.debut
        self.fin = cdg.fin
        self.liste_cours = user.groupe.liste_cours()
        self.rang = self.liste_cours.index(self.cours)
        self.titre = self.cours.titre(self.user.langue)
        self.modules = [UserModule(self.user,m)
                for m in self.cours.liste_modules()]

    def date_validation(self):
        """
        Renvoie la date de validation du cours
        False s'il n'est pas validé
        """
        #TODO Rajouter le test sur les devoirs aussi
        dates =  [m.date_validation() for m in self.modules]
        if False in dates:
            return False
        else:
            return max(dates)

    def valide_en_retard(self):
        if self.date_validation():
            return self.date_validation() > self.fin
        return False

    def en_retard(self):
        if self.fin and not self.date_validation():
            return self.fin < datetime.datetime.now()

    def prec(self):
        """
        Renvoie l'objet UserCours précédent
        """
        if self.rang > 0:
            return UserCours(self.user, self.liste_cours[self.rang-1])
        else:
            return None

    def is_open(self):
        """
        Renvoie True si le cours est ouvert :
        - tous les cours sont ouverts pour le groupe
        - ce cours est le premier pour le groupe
        - le cours précédent est validé
        """
        if self.user.groupe.is_open:
            return True
        if self.rang == 0:
            return True
        return self.prec().date_validation()

    def state(self):
        """
        Renvoie un message sur l'état du cours :
        - validé le
        - à valider pour le
        - ouvert à partir du
        - rien (si ouvert et commencé)
        """
        if self.debut > datetime.datetime.now():
            return _("This course will not open before %s") % self.debut.strftime("%d/%m/%Y")
        valide = self.date_validation()
        if valide:
            return _("Completed on %s") % valide.strftime("%d/%m/%Y")
        elif self.fin:
            return _("Deadline is %s") % self.fin.strftime("%d/%m/%Y")
        else:
            return ""

