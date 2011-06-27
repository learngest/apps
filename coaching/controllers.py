# -*- encoding: utf-8 -*-

import datetime

from django.utils.translation import ugettext as _
#from django.core.cache import cache
from django.conf import settings

from coaching.models import Utilisateur, ModuleValide, Resultat, Work, WorkDone, CoursDuGroupe, Prof, AutresDocs
from learning.controllers import UserModule, UserCours
from testing.controllers import UserExam
from learning.models import Cours
from testing.models import Examen

class ProfCours(object):
    """
    Controller d'un cours géré par un prof pour un groupe
    """
    def __init__(self, prof, gcp):
        self.prof = prof
        self.groupe = gcp.groupe
        self.cours = gcp.cours
        self.nb_modules = len(self.cours.liste_modules())
        self.titre = gcp.cours.titre(prof.langue)

    def users(self):
        """
        Return cours users
        """
        return [UserState(u, self.cours) for u in
                Utilisateur.objects.filter(groupe=self.groupe)]

def filters(admin, groupe, selected=None):
    """
    Filtres de tri du groupe par performance
    """

    def titre(c):
        if c[1]:
            return _('%(titre)s - %(nb)s or less') \
                    % {'titre':c[0].titre(admin.langue),'nb':c[1]}
        return '%s - %s' % (c[0].titre(admin.langue),c[1])

    filters = [{'titre':_('Everything'), 'query':'', 'selected': selected==None}]
    for c in groupe.filtres():
        query = 'current__id=%s&nb_valides__lte=%s' % (c[0].id, c[1])
        filters.append({
          'titre': titre(c),
          'query': query,
          'selected': selected==query,
          })
    return filters

class AdminGroupe(object):
    """
    Controller du groupe d'un administrateur
    ou d'un assistant
    """
    def __init__(self, admin, groupe, selection=None):
        self._users = -1
        self.admin = admin
        self.groupe = groupe
        self.selection = selection
        self.nom = self.groupe.nom
        self.is_open = self.groupe.is_open
        self.is_demo = self.groupe.is_demo
        self.get_absolute_url = self.groupe.get_absolute_url()
        self.get_admin_url = self.groupe.get_admin_url()
        self.nb_logins = Utilisateur.objects.filter(groupe=groupe).count()
        self.nb_cours = self.groupe.cours.count()
        self.nb_works = Work.objects.filter(groupe=self.groupe).count()
        self.nb_exams = Examen.objects.filter(groupe=self.groupe).count()
        self._courant = -1
        self._nb_users_pb = -1

    def users(self):
        """
        Return active groups users, as list of dict
        """
        if self._users == -1:
            lookup = {'groupe': self.groupe,}
            if self.selection:
                lookup.update(self.selection)
            self._users = [UserState(u) for u in
                    Utilisateur.objects.filter(is_active=1).filter(**lookup)]
        return self._users

    def filtres(self):
        """
        Filtres applicables à ce groupe
        """
        courants = list(set(
            [(u.cours_courant().cours, u.nb_modules_valides_in_current())
            for u in self.users() if u.cours()]))
        tous_les_cours = list(self.groupe.cours.order_by('coursdugroupe__rang'))
        for c in courants:
            c[0].rang = tous_les_cours.index(c[0])
        courants.sort(key=lambda x: (x[0].rang,x[1]))
        return courants

    def workdone(self):
        """
        Return group assignments to download,
        as a list of zipfiles
        """
        import os.path
        lworkdone = []
        for c in self.groupe.cours.all():
            zipname = 'g%d-%s.zip' % (self.groupe.id, c.slug)
            zipfile = os.path.join(settings.MEDIA_ROOT,
                    settings.WORKDONE_DIR,zipname)
            if os.path.exists(zipfile):
                lworkdone.append(zipname)
        return lworkdone

    def courant(self):
        """
        Renvoie l'objet cours courant
        """
        if self._courant==-1:
            curdate = datetime.datetime.now()
            self._courant = None
            for cdg in CoursDuGroupe.objects.filter(groupe=self.groupe):
                if cdg.debut and cdg.debut <= curdate:
                    if cdg.fin and cdg.fin >= curdate:
                        self._courant = cdg
                        break
            if self._courant:
                try:
                    self._courant = Cours.objects.get(id=cdg.cours.id)
                    self._courant.titre = self._courant.titre(self.admin.langue)
                except Cours.DoesNotExist:
                    self._courant = "Not found"
        return self._courant

    def nb_users_pb(self):
        """
        Renvoie le nb d'utilisateurs qui sont en retard
        et n'ont pas travaillé depuis au moins une semaine
        """
        if self._nb_users_pb==-1:
            datelimite = datetime.datetime.now()-datetime.timedelta(7)
            self._nb_users_pb = Utilisateur.objects.filter(
                    groupe=self.groupe,
                    nb_actuel__gt=0,
                    last_login__lt=datelimite,
                    ).count()
        return self._nb_users_pb

class UserState(object):
    """
    Controller d'un utilisateur avec état des performances
    """
    def __init__(self, user, le_cours=None):
        self.user = user
        self.le_cours = le_cours
        self.get_full_name = user.get_full_name()
        self.get_name = '%s %s' % (user.last_name, user.first_name)
        self.email = user.email
        self.get_absolute_url = user.get_absolute_url()
        self.last_login = user.last_login
        self._state = None
        self._exams = []
        self._cours = []
        self._nb_cours = None
        self._nb_travaux = None

    def exams(self):
        if not self._exams:
            self._exams = [UserExam(self.user, e)
                for e in Examen.objects.filter(
                    groupe=self.user.groupe).order_by('cours')]
        return self._exams

    def resultat(self, exam=None):
        if exam:
            return UserExam(self.user, exam).score()
        return None

    def cours(self):
        if not self._cours:
            self._cours = [UserCours(self.user, c)
                for c in self.user.groupe.cours.order_by('coursdugroupe__rang')]
        return self._cours

    def recalcule_tout(self, sauver=True):
        """
        Recalcule tous les éléments de performance
        stockés de l'utilisateur
        """
        self.nb_travaux_rendus(recalcul=True, sauve=False)
        self.nb_cours_valides(recalcul=True, sauve=False)
        self.nb_cours_en_retard(recalcul=True, sauve=False)
        self.nb_cours_valides_en_retard(recalcul=True, sauve=False)
        self.cours_courant(recalcul=True,sauve=False)
        self.nb_modules_in_current(recalcul=True,sauve=False)
        self.nb_modules_valides_in_current(recalcul=True,sauve=False)
        if sauver:
            self.user.save()

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
                        if uc.debut:
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
                        else:
                            self.user.current = uc.cours
                            if sauve:
                                self.user.save()
                            return uc
                self.user.current = ucs[-1].cours
                if sauve:
                    self.user.save()
                return ucs[-1]
        return UserCours(self.user, self.user.current)

    def nb_modules_valides(self):
        """
        Nb de module validés dans self.le_cours
        """
        if self.le_cours:
            return len(UserCours(self.user, self.le_cours).modules_valides())
        return None

    def nb_modules_in_current(self, recalcul=False, sauve=True):
        """
        Nombre de modules à valider dans le usercours courant
        stocké dans Utilisateur.nb_modules ou recalculé
        """
        if self.user.nb_modules is None or recalcul:
            courant = self.cours_courant()
            if courant:
                self.user.nb_modules = len(courant.modules_a_valider())
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

    def state(self):
        """
        True s'il y a un problème :
        - actuellement en retard
        - compte inactif
        - compte ferme dans moins d'une semaine
        """
        if self._state is None:
            self._state = self.is_inactif() \
                    or self.fermeture_prochaine() or self.nb_cours_en_retard()
        return self._state

    def workdone(self):
        """
        Return user's assignments to download,
        as a zipfile
        """
        import os.path
        zipname = 'g%d-%s.zip' % (self.user.groupe.id, self.user.username)
        zipfile = os.path.join(settings.MEDIA_ROOT,
                settings.WORKDONE_DIR,zipname)
        if os.path.exists(zipfile):
            return zipname


class AdminCours(object):
    """
    Controller d'un cours pour un administrateur
    """
    def __init__(self, user, cours, groupe):
        self._usermodules = -1
        self._assignments = -1
        self._autres_docs = -1
        self.user = user
        self.cours = cours
        self.groupe = groupe
        cdg = CoursDuGroupe.objects.get(cours=self.cours,groupe=self.groupe)
        self.debut = cdg.debut
        self.fin = cdg.fin
        self._liste_cours = []

    def _get_liste_cours(self):
        if not self._liste_cours:
            self._liste_cours = list(
                    self.groupe.cours.order_by('coursdugroupe__rang'))
        return self._liste_cours

    liste_cours = property(_get_liste_cours)

    def _get_rang(self):
        return self.liste_cours.index(self.cours)

    rang = property(_get_rang)

    def profs(self):
        return [prof.utilisateur for prof in
                Prof.objects.filter(groupe=self.groupe,cours=self.cours)]

    def titre(self):
        return self.cours.titre(self.user.langue)

    def modules(self):
        if self._usermodules == -1:
            self._usermodules = [UserModule(self.user, m) 
                    for m in self.cours.liste_modules()]
        return self._usermodules

    def autres_docs(self):
        if self._autres_docs == -1:
            self._autres_docs = AutresDocs.objects.filter(
                    groupe=self.groupe, cours = self.cours)
        return self._autres_docs

    def assignments(self):
        if self._assignments == -1:
            self._assignments = Work.objects.filter(
                cours=self.cours,
                groupe=self.groupe)
        return self._assignments

    def prec(self):
        """
        Renvoie l'objet UserCours précédent
        """
        if self.rang > 0:
            return UserCours(self.user, self.liste_cours[self.rang-1])
        else:
            return None

