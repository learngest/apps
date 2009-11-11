# -*- encoding: utf-8 -*-

import datetime

from django.utils.translation import ugettext as _
from django.core.cache import cache

from coaching.models import CoursDuGroupe, Work, WorkDone
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
        self.titre = self.module.titre(self.user.langue)
        self.contents = Contenu.objects.filter(module=self.module,
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
        dates =  [t.date_validation() for t in self.tests()]
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
        liste_cours = self.user.groupe.cours.all()
        for c in liste_cours:
            if self.module in [mc.module for mc in c.modulecours_set.all()]:
                return c
        return None

    def is_open(self):
        """
        Renvoie True si le module est ouvert
        """
        if self.user.statut == 3:
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
        except WorkDone.DoesNotExist:
            self.date_remise = False
            self.signature = None


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
        self.liste_cours = list(user.groupe.cours.order_by('coursdugroupe__rang'))
        self.rang = self.liste_cours.index(self.cours)
        self.titre = self.cours.titre(self.user.langue)

    def modules(self):
        return [UserModule(self.user, m) for m in self.cours.liste_modules()]

    def assignments(self):
        return [UserWork(self.user, w) for w in Work.objects.filter(
            cours=self.cours,
            groupe=self.user.groupe)]

    def modules_valides(self):
        return [um for um in self.modules() if um.date_validation()]

    def date_validation(self):
        """
        Renvoie la date de validation du cours
        False s'il n'est pas validé
        None s'il n'y a pas de tests dans le cours
        """
        dates =  [m.date_validation() for m in self.modules()]
        dates.extend([w.date_remise for w in self.assignments()])
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
        if self.user.statut > 0:
            return True
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

