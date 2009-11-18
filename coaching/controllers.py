# -*- encoding: utf-8 -*-

import datetime

from django.utils.translation import ugettext as _
#from django.core.cache import cache
from django.conf import settings

from coaching.models import Utilisateur, ModuleValide, Resultat, Work, WorkDone
from learning.controllers import UserModule, UserCours

class AdminGroupe(object):
    """
    Controller du groupe d'un administrateur
    """
    def __init__(self, admin, groupe):
        self.admin = admin
        self.groupe = groupe
        self.nom = self.groupe.nom
        self.is_open = self.groupe.is_open
        self.is_demo = self.groupe.is_demo
        self.get_absolute_url = self.groupe.get_absolute_url()
        self.nb_logins = Utilisateur.objects.filter(groupe=groupe).count()
        #self.nb_cours = self.groupe.coursdugroupe_set.all().count()
        self.nb_cours = self.groupe.cours.count()
        self.nb_works = Work.objects.filter(groupe=self.groupe).count()

    def users(self):
        """
        Return groups users, as list of dict
        """
        return [UserState(u) for u in
                Utilisateur.objects.filter(groupe=self.groupe)]

    def workdone(self):
        """
        Return group assignments to download,
        as a list of zipfiles
        """
        import os.path
        lworkdone = []
        for c in self.groupe.cours:
            zipname = 'g%d-%s.zip' % (self.groupe.id, c.slug)
            zipfile = os.path.join(settings.MEDIA_ROOT,
                    settings.WORKDONE_DIR,zipname)
            if os.path.exists(zipfile):
                lwordone.append(zipname)
        return lworkdone


class UserState(object):
    """
    Controller d'un utilisateur avec état des performances
    """
    def __init__(self, user):
        self.user = user
        self.get_full_name = user.get_full_name()
        self.email = user.email
        self.get_absolute_url = user.get_absolute_url()
        self.last_login = user.last_login
        self._cours = []
        self._nb_cours = None
        self._nb_travaux = None

    def cours(self):
        if not self._cours:
            self._cours = [UserCours(self.user, c)
                for c in self.user.groupe.cours.order_by('coursdugroupe__rang')]
        return self._cours

    def nb_cours(self):
        """
        Retourne le nombre de cours auxquels l'utilisateur est inscrit
        """
        if not self._nb_cours:
            self._nb_cours = self.user.groupe.cours.count()
        return self._nb_cours

    def nb_cours_valides(self, recalcul=False, sauve=True):
        """
        Nombre de cours validés, 
        stocké dans Utilisateur.nb_cours_valides ou recalculé
        """
        if self.user.nb_cours_valides is None or recalcul:
            self.user.nb_cours_valides = \
                    len([1 for uc in self.cours() if uc.valide])
            if sauve:
                self.user.save()
        return self.user.nb_cours_valides

    def nb_cours_en_retard(self, recalcul=False, sauve=True):
        """
        Nb de cours actuellement en retard,
        stocké dans Utilisateur.nb_actuel ou recalculé
        """
        if self.user.nb_actuel is None or recalcul:
            self.user.nb_actuel = len([1 for uc in self.cours() if uc.en_retard()])
        return self.user.nb_actuel

    def nb_cours_valides_en_retard(self, recalcul=False, sauve=True):
        """
        Nombre de cours validés en retard,
        stocké dans Utilisateur.nb_retards ou recalculé
        """
        if self.user.nb_retards is None or recalcul:
            self.user.nb_retards = \
                len([1 for uc in self.cours() if uc.valide_en_retard()])
            if sauve:
                self.user.save()
        return self.user.nb_retards

    def nb_travaux(self):
        """
        Retourne le nombre de travaux à rendre par cet utilisateur
        """
        if not self._nb_travaux:
            self._nb_travaux = Work.objects.filter(groupe=self.user.groupe).count()
        return self._nb_travaux

    def nb_travaux_rendus(self, recalcul=False, sauve=True):
        """
        Nombre de travaux rendus, 
        stocké dans Utilisateur.nb_travaux_rendus ou recalculé
        """
        if self.user.nb_travaux_rendus is None or recalcul:
            self.user.nb_travaux_rendus = \
                    WorkDone.objects.filter(utilisateur=self.user).count()
            if sauve:
                self.user.save()
        return self.user.nb_travaux_rendus

    def cours_courant(self, recalcul=False, sauve=True):
        """
        UserCours "courant", c-a-d celui qui suit le dernier validé
        s'il est ouvert, le dernier validé sinon.
        Le cours courant est stocké dans Utilisateur.current 
        """
        if self.user.current is None or recalcul:
            ucs = self.cours()
            if not ucs:
                return None
            else:
                for uc in ucs:
                    if uc.valide is False:
                        if uc.debut <= datetime.datetime.now():
                            self.user.current = uc.cours
                            if sauve:
                                self.user.save()
                            return uc
                        else:
                            ucurrent = uc.prec() or ucs[0]
                            self.user.current = ucurrent.cours
                            if sauve:
                                self.user.save()
                            return ucurrent
                self.user.current = ucs[-1].cours
                if sauve:
                    self.user.save()
                return ucs[-1]
        return UserCours(self.user, self.user.current)

    def nb_modules_in_current(self, recalcul=False, sauve=True):
        """
        Nombre de modules dans le usercours courant
        stocké dans Utilisateur.nb_modules ou recalculé
        """
        if self.user.nb_modules is None or recalcul:
            courant = self.cours_courant()
            if courant:
                self.user.nb_modules = len(courant.modules())
            else:
                self.user.nb_modules = 0
            if sauve:
                self.user.save()
        return self.user.nb_modules

    def nb_modules_valides_in_current(self, recalcul=False, sauve=True):
        """
        Nombre de modules validés dans le usercours "courant"
        stocké dans Utilisateur.nb_valides ou recalculé
        """
        if self.user.nb_valides is None or recalcul:
            courant = self.cours_courant()
            if courant:
                self.user.nb_valides = len(courant.modules_valides())
            else:
                self.user.nb_valides = 0
            if sauve:
                self.user.save()
        return self.user.nb_valides

    def fermeture_prochaine(self):
        """
        True si le compte de l'utilisateur ferme dans moins de 7 jours
        """
        now = datetime.datetime.now()
        next_week = now + datetime.timedelta(days=7)
        return self.user.fermeture > now and self.user.fermeture < next_week

    def is_inactif(self):
        """
        True si le compte de l'utilisateur est fermé ou inactif
        """
        now = datetime.datetime.now()
        return not self.user.is_active or self.user.fermeture < now

