# -*- encoding: utf-8 -*-

import datetime

from django.utils.translation import ugettext as _
#from django.core.cache import cache

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
        self.nb_cours = self.groupe.coursdugroupe_set.all().count()
        self.nb_works = Work.objects.filter(groupe=self.groupe).count()

    def users(self):
        """
        Return groups users, as list of dict
        """
        return [UserState(u) for u in
                Utilisateur.objects.filter(groupe=self.groupe)]

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

    def _usercours(self):
        return [UserCours(self.user, c) for c in self.user.groupe.liste_cours()]

    def nb_cours_valides(self):
        """
        Nombre de cours validés, stocké dans Utilisateur ou recalculé
        """
        if self.user.nb_cours_valides is None:
            print "calcul nb_cours_valides"
            self.user.nb_cours_valides = \
                    len([1 for uc in self._usercours() if uc.date_validation()])
            self.user.save()
        return self.user.nb_cours_valides

    def nb_travaux_rendus(self):
        """
        Nombre de travaux rendus, stocké dans Utilisateur ou recalculé
        """
        if self.user.nb_travaux_rendus is None:
            print "calcul nb_travaux_rendus"
            self.user.nb_travaux_rendus = \
                    WorkDone.objects.filter(utilisateur=self.user).count()
            self.user.save()
        return self.user.nb_travaux_rendus

    def cours_courant(self):
        """
        Retourne le usercours "courant", c-a-d celui qui suit le dernier validé
        """
        ucs = self._usercours()
        if not ucs:
            return None
        else:
            for uc in ucs:
                if not uc.date_validation():
                    return uc
            return ucs[-1]

    def nb_modules_valides_in_current(self):
        """
        Retourne le nb de modules validés dans le usercours "courant"
        """
        courant = self.cours_courant()
        valides = len(courant.modules_valides())
        total = len(courant.modules())
        return "%d / %d" % (valides, total)

    def state(self):
        state = []
        last_modules = ModuleValide.objects.filter(
                utilisateur=self.user).order_by('-date')
        if last_modules:
            last_module = last_modules[0]
            last_module_str = {
                    'titre':last_module.module.titre(self.user.langue), 
                    'date':last_module.date
                    }
            last_module_str = _("Module %(titre)s completed on %(date)s") \
                    % last_module_str
            um = UserModule(self.user, last_module)
            uc = UserCours(self.user, um.cours())
            uc.datev = uc.date_validation()
            if uc.date_v:
                last_cours_str = {'titre':uc.titre, 'date':uc.date_v}
                last_cours_str = _("Course %(titre)s completed on %(date)s") \
                        % last_cours_str
                state.append(last_cours_str)
            else:
                uc = uc.prec()
                if uc:
                    uc.datev = uc.date_validation()
                    if uc.date_v:
                        last_cours_str = {'titre':uc.titre, 'date':uc.date_v}
                        last_cours_str = _("Course %(titre)s completed on %(date)s") \
                                % last_cours_str
                        state.append(last_cours_str)
                        state.append(last_module_str)
        else:
            last_trys = Resultat.objects.filter(
                    utilisateur=self.user).order_by('-date')
            if last_trys:
                last_try = last_trys[0]
                last_try_str = last_try.granule.module.titre(self.user.langue)
                last_try_str = _("Working on module %s") % last_try_str
                state.append(last_try_str)
        return state

    def problems(self):
        problems = []
        cours = [UserCours(self.user, cours) 
                for cours in self.user.groupe.liste_cours()]
        valides_en_retard = 0
        en_retard = []
        for uc in cours:
            if uc.valide_en_retard():
                valides_en_retard += 1
            if uc.en_retard():
                retard_str = _("Late on %s") % uc.titre
                en_retard.append(retard_str)
        if valides_en_retard:
            problems.append(_("%d courses completed late") % valides_en_retard)
        problems.extend(en_retard)
        now = datetime.datetime.now()
        next_week = now + datetime.timedelta(days=7)
        if self.user.fermeture < next_week:
            if self.user.fermeture < now:
                pb = _("Closed on %s") % self.user.fermeture.strftime('%Y/%m/%d')
            else:
                pb = _("Will close on %s") % self.user.fermeture.strftime('%Y/%m/%d')
            problems.append(pb)
        return problems

        