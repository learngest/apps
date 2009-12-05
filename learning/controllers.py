# -*- encoding: utf-8 -*-

import datetime

from django.utils.translation import ugettext as _
from django.core.cache import cache
from django.conf import settings

from coaching.models import CoursDuGroupe, Work, WorkDone, AutresDocs, Prof
from learning.models import Contenu
from testing.models import Granule
from testing.controllers import UserGranule

class UserModule(object):
    """
    Controller d'un module pour un utilisateur
    """
    def __init__(self, user, module):
        self.user = user
        self.module = module
        self._date_validation = -1

    def titre(self):
        return self.module.titre(self.user.langue)

    def contents(self):
        return Contenu.objects.filter(
                module=self.module,
                langue=self.user.langue).order_by('type')

    def tests(self):
        return [UserGranule(self.user,g) \
                for g in Granule.objects.filter(module=self.module)]

    def date_validation(self):
        """
        Renvoie la date de validation du module
        False s'il n'est pas validé
        None si le module n'a pas de tests
        """
        if self._date_validation == -1:
            dates =  [t.date_validation() for t in self.tests()]
            if not dates:
                self._date_validation = None
                return self._date_validation
            if False in dates:
                self._date_validation = False
            else:
                self._date_validation = max(dates)
        return self._date_validation

    def cours(self):
        """
        Renvoie l'objet Cours auquel appartient le module pour
        cet utilisateur
        """
        liste_cours = self.user.groupe.cours.all()
        for c in liste_cours:
            if self.module in [mc.module for mc in c.modulecours_set.all()]:
                return c
        return None

    def is_open(self):
        """
        Renvoie True si le module est ouvert
        """
        if self.user.statut == settings.STAFF:
            return True
        if not self.cours():
            return False
        if UserCours(self.user, self.cours()).is_open():
            return True
        return False


class UserWork(object):
    """
    Controller d'un devoir pour un utilisateur
    """
    def __init__(self, user, work):
        self.user = user
        self.work = work
        self.titre = self.work.titre
        try:
            wd = WorkDone.objects.get(utilisateur=self.user, work=self.work)
            self.date_remise = wd.date
            self.signature = wd.signature
            self.url = wd.fichier.url
        except WorkDone.DoesNotExist:
            self.date_remise = False
            self.signature = None
            self.url = None


class UserCours(object):
    """
    Controller d'un cours pour un utilisateur
    """
    def __init__(self, user, cours):
        self._usermodules = -1
        self._usermodules_a_valider = -1
        self._assignments = -1
        self._autres_docs = -1
        self._date_validation = -1
        self.user = user
        self.cours = cours
        cdg = CoursDuGroupe.objects.get(cours=self.cours,groupe=self.user.groupe)
        self.debut = cdg.debut
        self.fin = cdg.fin
        self._liste_cours = []

    def _get_liste_cours(self):
        if not self._liste_cours:
            self._liste_cours = list(
                    self.user.groupe.cours.order_by('coursdugroupe__rang'))
        return self._liste_cours

    liste_cours = property(_get_liste_cours)

    def _get_rang(self):
        return self.liste_cours.index(self.cours)

    rang = property(_get_rang)

    def profs(self):
        return [prof.utilisateur for prof in
                Prof.objects.filter(groupe=self.user.groupe,cours=self.cours)]

    def titre(self):
        return self.cours.titre(self.user.langue)

    def modules(self):
        if self._usermodules == -1:
            self._usermodules = [UserModule(self.user, m) 
                    for m in self.cours.liste_modules()]
        return self._usermodules

    def modules_a_valider(self):
        if self._usermodules_a_valider == -1:
            self._usermodules_a_valider = [m for m in self.modules()
                    if len(m.tests())]
        return self._usermodules_a_valider

    def autres_docs(self):
        if self._autres_docs == -1:
            self._autres_docs = AutresDocs.objects.filter(
                    groupe=self.user.groupe, cours = self.cours)
        return self._autres_docs

    def assignments(self):
        if self._assignments == -1:
            self._assignments = [UserWork(self.user, w)
                for w in Work.objects.filter(
                cours=self.cours,
                groupe=self.user.groupe)]
        return self._assignments

    def modules_valides(self):
        return [um for um in self.modules() if um.date_validation()]

    def date_validation(self):
        """
        Renvoie la date de validation du cours
        False s'il n'est pas validé
        None s'il n'y a pas de tests dans le cours
        """
        if self._date_validation == -1:
            dates =  [m.date_validation() for m in self.modules()
                                if m.date_validation() is not None]
            dates.extend([w.date_remise for w in self.assignments()])
            if dates:
                if False in dates:
                    self._date_validation = False
                else:
                    self._date_validation = max(dates)
            else:
                self._date_validation = None
        return self._date_validation

    valide = property(date_validation)

    def valide_en_retard(self):
        if self.valide:
            return self.valide > self.fin
        return False

    def en_retard(self):
        if self.fin and not self.valide:
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
        - le cours précédent est validé et la date d'ouverture est passée
        """
        if self.user.statut > settings.ASSISTANT:
            return True
        if self.user.groupe.is_open:
            return True
        if self.rang == 0:
            return True
        if self.prec().valide:
            if self.debut:
                if datetime.datetime.now() >= self.debut:
                    return True
                else:
                    return False
            else:
                return True
        return False

            
        return self.prec().valide

    def state(self):
        """
        Renvoie un message sur l'état du cours :
        - validé le
        - à valider pour le
        - ouvert à partir du
        - rien (si ouvert et commencé)
        """
        if self.debut > datetime.datetime.now():
            return _("This course will not open before %s") \
                    % self.debut.strftime("%d/%m/%Y")
        if self.valide:
            if self.valide_en_retard():
                return _("<span class=\"red\">Completed late on %s</span>") \
                            % self.valide.strftime("%d/%m/%Y")
            else:
                return _("Completed on %s") % self.valide.strftime("%d/%m/%Y")
        elif self.fin:
            if self.en_retard():
                return _("<span class=\"red\">Late! Deadline was %s</span>") \
                             % self.fin.strftime("%d/%m/%Y")
            else:
                return _("Deadline is %s") % self.fin.strftime("%d/%m/%Y")
        else:
            return ""

