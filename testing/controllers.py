# -*- encoding: utf-8 -*-

import sys

from django.utils.translation import ugettext as _
from django.core.cache import cache

from testing.models import Question
from coaching.models import GranuleValide, ModuleValide, Resultat

class UserGranule(object):
    """
    Controller d'une granule de test pour un utilisateur
    """
    def __init__(self, user, granule):
        self.user = user
        self.granule = granule
        self.get_absolute_url = self.granule.get_absolute_url()
        self.titre = self.granule.titre(self.user.langue)
        resultats = Resultat.objects.filter(utilisateur=self.user,
                        granule=self.granule).order_by('-score')
        if resultats:
            self.nb_tries = resultats.count()
            self.best_score = resultats[0].score
            self.str_best_score = "%2d %%" % self.best_score
            self.best_score_date = resultats[0].date
        else:
            self.nb_tries = 0
            self.best_score = 0
            self.str_best_score = ''
            self.best_score_date = None

    def date_validation(self):
        """
        Renvoie la date de validation du test
        False s'il n'est pas validé
        """
        try:
            v =GranuleValide.objects.get(utilisateur=self.user,
                                            granule=self.granule)
        except GranuleValide.DoesNotExist:
            return False
        return v.date

class UserTest(object):
    """
    Controller d'un test pour un utilisateur et
    une granule donnés
    """
    REP = " <input type=\"text\" size=\"15\" name=\"rep%d\" /> "
    HID_DICT = "<input type=\"hidden\" value=\"%s\" name=\"dic%d\" />"
    HID_REP = "<br /><input type=\"hidden\" value=\"0\" name=\"rep%d\" />"
    RADIO = "<br /><input type=\"radio\" value=\"%s\" name=\"rep%d\" />&nbsp;%s"
    CHECK = "<br /><input type=\"checkbox\" value=\"%s\" name=\"rep%d\" />&nbsp;%s"

    def __init__(self, user, granule, langue):
        self.user = user
        self.granule = granule
        self.langue = langue
        self.titre = self.granule.titre(self.langue)
        self.enonces = self._enonces()

    def _enonces(self):
        """
        Retourne le code html des énoncés du test, avec leurs questions
        """
        questions = \
            Question.objects.filter(granule=self.granule, 
                    langue=self.langue).order_by('?')[:self.granule.nbq]
        if not questions:
            questions = \
                Question.objects.filter(granule=self.granule, 
                        langue='fr').order_by('?')[:self.granule.nbq]
            self.user.message_set.create(
                message=_('We are sorry, this content is not available in your preferred language.'))
        enonces = {}
        for q in questions:
            enonces.setdefault(q.enonce.id,{})
            enonces[q.enonce.id]['libel'] = q.enonce.libel
            if not 'questions' in enonces[q.enonce.id]:
                enonces[q.enonce.id]['questions'] = []
            enonces[q.enonce.id]['questions'].append(
                    getattr(self, "_output_%s" % q.typq)(q))
        return enonces.values()

    def _output_rnd(self, question):
        import random
        phrase, dico = question.libel.split(" % ")
        phrase = eval(phrase)
        dico = eval(dico)
        phrase = phrase % dico
        rep = self.REP % question.id
        hidden = self.HID_DICT % (dico,question.id)
        return " ".join((phrase,rep,hidden))

    def _output_exa(self, question):
        rep = self.REP % question.id
        return question.libel.replace("<REPONSE>",rep)

    def _output_num(self, question):
        return self.output_exa(question)

    def _output_qrm(question):
        if sys.version_info[1]==3:
            reponses = '\n'.join([self.CHECK % (r.id, question.id, r)
                                for r in question.reponse_set.all()])
        else:
            reponses = '\n'.join([self.CHECK % (r.id, question.id, r.valeur)
                                for r in question.reponse_set.all()])
        hidden = self.HID_REP % question.id
        return '\n'.join((question.libel,hidden,reponses))

    def _output_qcm(question):
        if sys.version_info[1]==3:
            reponses = '\n'.join( [self.RADIO % (r.id, question.id, r)
                                for r in question.reponse_set.all()])
        else:
            reponses = '\n'.join( [self.RADIO % (r.id, question.id, r.valeur)
                                for r in question.reponse_set.all()])
        hidden = self.HID_REP % question.id
        return '\n'.join((question.libel,hidden,reponses))

class UserSubmittedTest(object):
    """
    Controller des réponses à test soumises via POST
    """
    def __init__(self, request):
        self.user = request.user
        self.request = request
        self.max = 0
        self.total = 0
        self.valide = False

    def _clean(self, astring, bad=(' ','%')):
        for badchar in bad:
            astring = astring.replace(badchar,'')
        return astring

    def _set_qd(self, q, rep):
        qd = {}
        qd['libel'] = q.libel.replace("<REPONSE>","...")
        qd['reponse'] = rep or _('nothing')
        return qd

    def _noter_exa(self, q, rep):
        rep = rep[-1]
        qd = self._set_qd(q, rep)
        r = q.reponse_set.all()[0]
        self.max += r.points
        if rep:
            rep = self._clean(rep).replace(',','.').rstrip('0')
            r.valeur = self._clean(r.valeur).replace(',','.').rstrip('0')
            if rep == r.valeur:
                qd['points'] = r.points
                self.total += r.points
            else:
                qd['points'] = '0'
        else:
            qd['points'] = '0'
        return qd

    def _noter_num(self, q, rep):
        rep = rep[-1]
        qd = self._set_qd(q, rep)
        r = q.reponse_set.all()[0]
        self.max += r.points
        # seuls les chiffres avant le séparateur décimal sont significatifs
        rep = rep.replace('%','')
        rep = rep.replace(',','.').strip()
        r.valeur = r.valeur.replace(',','.').strip()
        if rep.startswith(r.valeur.split('.')[0]):
            qd['points'] = r.points
            self.total += r.points
        else:
            qd['points'] = '0'
        return qd

    def _noter_rnd(self, q, rep):
        rep = rep[-1]
        qd = self._set_qd(q, rep)
        r = q.reponse_set.all()[0]
        self.max += r.points
        phrase, dico = q.libel.split(" % ")
        dico = ''.join(('dic',str(q.id)))
        dico = eval(self.request.POST[dico])
        qd['libel'] = eval(phrase) % dico
        for k,v in dico.items():
            locals()[k] = v
        r.valeur = '%f' % eval(r.valeur)
        if rep:
            rep = self._clean(rep).replace(',','.').rstrip('0')
            r.valeur = self._clean(r.valeur).replace(',','.').rstrip('0')
            # on teste sur 5 chiffres significatifs max + le point décimal
            if rep[:6] == r.valeur[:6]:
                qd['points'] = r.points
                self.total += r.points
            else:
                qd['points'] = '0'
        else:
            qd['points'] = '0'
        return qd

    def _noter_qcm(self, q, rep):
        rep = rep[-1]
        qd = self._set_qd(rep)
        for r in q.reponse_set.all():
            if int(rep) == r.id:
                self.total += r.points
                qd['points'] = r.points
                qd['reponse'] = r.valeur
            if r.points > 0:
                self.max += r.points
        # si pas de réponse
        if not 'points' in qd:
            qd['points'] = 0
            qd['reponse'] = _('nothing')
        return qd

    def _noter_qrm(self, q, rep):
        qd = {}
        qd['libel'] = q.libel.replace("<REPONSE>","...")
        qd['reponse'] = ''
        for r in q.reponse_set.all():
            for rr in rep:
                if int(rr) == r.id:
                    self.total += r.points
                    qd['points'] = qd.get('points',0) + r.points
                    if qd['reponse']:
                        qd['reponse'] = '; '.join((qd['reponse'],r.valeur))
                    else:
                        qd['reponse'] = r.valeur
            if r.points > 0:
                self.max += r.points
        # si pas de réponse
        if not 'points' in qd:
            qd['points'] = 0
            qd['reponse'] = _('nothing')
        return qd

    def noter(self):
        """
        Note le test
        Retourne un tuple (score, score_max, validé ?)
        """
        import finance
        from learning.controllers import UserCours
        enonces = {}
        for quest,rep in self.request.POST.lists():
            if not quest.startswith('rep'):
                continue
            try:
                q = Question.objects.get(id=quest.replace('rep',''))
            except Question.DoesNotExist:
                continue
            enonces.setdefault(q.enonce.id,{})
            enonces[q.enonce.id]['libel'] = q.enonce.libel
            if not 'questions' in enonces[q.enonce.id]:
                enonces[q.enonce.id]['questions'] = []
            enonces[q.enonce.id]['questions'].append(
                    getattr(self, "_noter_%s" % q.typq)(q, rep))

        if self.total < 0:
            self.total = 0
        try:
            score = round(float(self.total)/self.max*100)
        except ZeroDivisionError:
            score = 0
        try:
            g = q.granule
        except UnboundLocalError:
            return HttpResponseRedirect('/')
        self.titre = g.titre(self.user.langue)
        r = Resultat(utilisateur=self.user, granule=g, score=score)
        r.save()
        self.valide = score >= q.granule.score_min
        if self.valide:
            GranuleValide.objects.get_or_create(
                    utilisateur=self.user, granule=g, defaults={'score': score})
            mvalide = True
            for gr in g.module.granule_set.all():
                if self.user.granulevalide_set.filter(granule=gr).count() == 0:
                    mvalide = False
                    break
            if mvalide:
                # TODO Maj nb_valides etc.
                # pb si on fait +=1 et que le module a déjà été validé
                modules_key = "Utilisateur.%s.liste_modules_autorises" % user.id
                cache.delete(modules_key)
                cours_key = "Utilisateur.%s.liste_cours_ouverts" % user.id
                cache.delete(cours_key)
                ModuleValide.objects.get_or_create(
                    utilisateur=self.user, module=g.module)
                uc = UserCours(request.user, request.user.current)
                if uc.date_validation():
                    request.user.nb_cours_valides += 1
                    try:
                        request.user.current = uc.liste_cours[uc.rang+1]
                    except IndexError:
                        pass
            request.user.save()

        self.enonces = enonces.values()
        return 
