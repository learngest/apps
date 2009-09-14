# -*- encoding: utf-8 -*-

import datetime

from django.utils.translation import ugettext as _
from coaching.models import CoursDuGroupe

class UserModule(object):
    """
    Controller d'un module pour un utilisateur
    """
    def __init__(self, user, module):
        self.user = user
        self.module = module
        self.titre = self.module.titre(self.user.langue)

    def date_validation(self):
        """
        Renvoie la date de validation du module
        False s'il n'est pas validé
        """
        #TODO
        return False

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
        self.modules = [UserModule(self.user,m) for m in self.cours.liste_modules()]

    def date_validation(self):
        """
        Renvoie la date de validation du cours
        False s'il n'est pas validé
        """
        dates =  [m.date_validation() for m in self.modules]
        if False in dates:
            return False
        else:
            return max(dates)

    def prec(self):
        """
        Renvoie l'objet UserCours précédent
        """
        return UserCours(self.user, self.liste_cours[self.rang-1])

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

