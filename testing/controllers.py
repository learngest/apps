# -*- encoding: utf-8 -*-

import sys

from django.utils.translation import ugettext as _
from django.core.cache import cache
from django.http import HttpResponseRedirect

from testing.models import Question, ExamCas, ExamQuestion
from coaching.models import GranuleValide, ModuleValide, Resultat, CoursDuGroupe
from coaching.models import ExamScore

import finance

REP = " <input type=\"text\" size=\"15\" name=\"rep%d\" /> "
HID_DICT = "<input type=\"hidden\" value=\"%s\" name=\"dic%d\" />"
HID_REP = "<br /><input type=\"hidden\" value=\"0\" name=\"rep%d\" />"
RADIO = "<br /><input type=\"radio\" value=\"%s\" name=\"rep%d\" />&nbsp;%s"
CHECK = "<br /><input type=\"checkbox\" value=\"%s\" name=\"rep%d\" />&nbsp;%s"

class UserGranule(object):
    """
    Controller d'une granule de test pour un utilisateur
    """
    def __init__(self, user, granule):
        self.user = user
        self.granule = granule
        self.get_absolute_url = self.granule.get_absolute_url()
        self._date_validation = -1
        self._resultats = -1
        self._perfs = []

    def titre(self):
        return self.granule.titre(self.user.langue)

    def resultats(self):
        if self._resultats == -1:
            self._resultats = Resultat.objects.filter(
                    utilisateur=self.user,
                    granule=self.granule).order_by('-score')
        return self._resultats

    def perfs(self):
        if not self._perfs:
            resultats = self.resultats()
            if resultats:
                nb_tries = resultats.count()
                best_score = resultats[0].score
                str_best_score = "%2d %%" % best_score
                best_score_date = resultats[0].date
            else:
                nb_tries = 0
                best_score = 0
                str_best_score = ''
                best_score_date = None
            self._perfs = [nb_tries, best_score, str_best_score, best_score_date]
        return self._perfs

    def nb_tries(self):
        return self.perfs()[0]

    def best_score(self):
        return self.perfs()[1]

    def str_best_score(self):
        return self.perfs()[2]

    def best_score_date(self):
        return self.perfs()[3]

    def date_validation(self):
        """
        Renvoie la date de validation du test
        False s'il n'est pas validé
        """
        if self._date_validation == -1:
            try:
                v = GranuleValide.objects.get(utilisateur=self.user,
                                                granule=self.granule)
                self._date_validation = v.date
            except GranuleValide.DoesNotExist:
                self._date_validation = False
        return self._date_validation

class UserTest(object):
    """
    Controller d'un test pour un utilisateur et
    une granule donnés
    """
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
            self.langue = 'fr'
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
        rep = REP % question.id
        hidden = HID_DICT % (dico,question.id)
        return " ".join((phrase,rep,hidden))

    def _output_exa(self, question):
        rep = REP % question.id
        return question.libel.replace("<REPONSE>",rep)

    def _output_num(self, question):
        return self.output_exa(question)

    def _output_qrm(self, question):
        if sys.version_info[1]==3:
            reponses = '\n'.join([CHECK % (r.id, question.id, r)
                                for r in question.reponse_set.all()])
        else:
            reponses = '\n'.join([CHECK % (r.id, question.id, r.valeur)
                                for r in question.reponse_set.all()])
        hidden = HID_REP % question.id
        return '\n'.join((question.libel,hidden,reponses))

    def _output_qcm(self, question):
        if sys.version_info[1]==3:
            reponses = '\n'.join( [RADIO % (r.id, question.id, r)
                                for r in question.reponse_set.all()])
        else:
            reponses = '\n'.join( [RADIO % (r.id, question.id, r.valeur)
                                for r in question.reponse_set.all()])
        hidden = HID_REP % question.id
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
        qd = self._set_qd(q, rep)
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
        self.get_absolute_url = g.get_absolute_url()
        r = Resultat(utilisateur=self.user, granule=g, score=score)
        r.save()
        self.valide = score >= q.granule.score_min
        if self.valide:
            # si déjà validé, on conserve l'ancien score
            try:
                GranuleValide.objects.get(
                        utilisateur=self.user,
                        granule=g)
            except GranuleValide.DoesNotExist:
                gv = GranuleValide(
                        utilisateur=self.user,
                        granule=g,
                        score=score)
                gv.save()
            mvalide = True
            for gr in g.module.granule_set.all():
                if self.user.granulevalide_set.filter(granule=gr).count() == 0:
                    mvalide = False
                    break
            if mvalide:
#                modules_key = \
#                        "Utilisateur.%s.liste_modules_autorises" % self.user.id
#                cache.delete(modules_key)
#                cours_key = "Utilisateur.%s.liste_cours_ouverts" % self.user.id
#                cache.delete(cours_key)
                # si module déjà validé on ne fait rien
                try:
                    ModuleValide.objects.get(
                            utilisateur=self.user,
                            module=g.module)
                except ModuleValide.DoesNotExist:
                    mv = ModuleValide(
                            utilisateur=self.user,
                            module=g.module)
                    mv.save()
                    self.user.nb_valides +=1
                    # module validé, est-ce que ça valide le cours ?
                    uc = UserCours(self.user, self.user.current)
                    if uc.valide:
                        self.user.nb_cours_valides += 1
                        # nouveau cours, raz nb_modules et nb_valides
                        self.user.nb_modules = None
                        self.user.nb_valides = 0
                        try:
                            self.user.current = uc.liste_cours[uc.rang+1]
                        except IndexError:
                            pass
            self.user.save()

        self.enonces = enonces.values()
        return 

class UserExam(object):
    """
    Controller d'un exam pour un utilisateur
    """
    def __init__(self, user, exam):
        self.user = user
        self.exam = exam
        self.titre = self.exam.titre
        self.debut = self.exam.debut
        self.fin = self.exam.fin
        if not (self.debut and self.fin):
            if self.exam.cours:
                try:
                    cdg = CoursDuGroupe.objects.get(
                            cours=self.exam.cours,groupe=self.user.groupe)
                    self.debut = self.debut or cdg.debut
                    self.fin = self.fin or cdg.fin
                except CoursDuGroupe.DoesNotExist:
                    pass

    def score(self):
        """
        Le score obtenu à l'examen, en pourcentage
        False si pas encore tenté
        """
        try:
            resultat = ExamScore.objects.get(
                    utilisateur=self.user, examen=self.exam)
            return resultat.score
        except ExamScore.DoesNotExist:
            return False

    def cas(self):
        """
        Retourne un cas pour cet examen ou
        False s'il est déjà tenté ou si non trouvé
        """
        if self.score():
            return False
        else:
            try:
                return ExamCas.objects.filter(examen=self.exam).order_by('?')[0]
            except IndexError:
                return False

    def is_open(self):
        """
        Un examen est ouvert si la date courant est entre début et fin
        et s'il n'a pas déjà été tenté.
        """
        import datetime
        now = datetime.datetime.now()
        if self.score():
            return False
        if self.debut and now < self.debut:
            return False
        if self.fin and now > self.fin:
            return False
        return True

class UserCase(object):
    """
    Controller d'un cas d'examen pour un user
    """
    def __init__(self, user, cas):
        self.user = user
        self.cas = cas
        self.titre = self.cas.titre
        self.texte = self.cas.texte
        self.enonces = self._enonces()

    def _enonces(self):
        """
        Retourne le code html des énoncés du cas, avec leurs questions
        """
        questions = \
            ExamQuestion.objects.filter(examen=self.cas)
        if not questions:
            self.user.message_set.create(
                message=_('Hmm, no questions for this case study.'))
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
        rep = REP % question.id
        hidden = HID_DICT % (dico,question.id)
        return " ".join((phrase,rep,hidden))

    def _output_exa(self, question):
        rep = REP % question.id
        return question.libel.replace("<REPONSE>",rep)

    def _output_num(self, question):
        return self.output_exa(question)

    def _output_qrm(self, question):
        if sys.version_info[1]==3:
            reponses = '\n'.join([CHECK % (r.id, question.id, r)
                                for r in question.reponse_set.all()])
        else:
            reponses = '\n'.join([CHECK % (r.id, question.id, r.valeur)
                                for r in question.reponse_set.all()])
        hidden = HID_REP % question.id
        return '\n'.join((question.libel,hidden,reponses))

    def _output_qcm(self, question):
        if sys.version_info[1]==3:
            reponses = '\n'.join( [RADIO % (r.id, question.id, r)
                                for r in question.reponse_set.all()])
        else:
            reponses = '\n'.join( [RADIO % (r.id, question.id, r.valeur)
                                for r in question.reponse_set.all()])
        hidden = HID_REP % question.id
        return '\n'.join((question.libel,hidden,reponses))

class UserSubmittedCase(object):
    """
    Controller des réponses à un cas
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
        r = q.examreponse_set.all()[0]
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
        qd = self._set_qd(q, rep)
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
        Note le cas
        """
        enonces = {}
        for quest,rep in self.request.POST.lists():
            if not quest.startswith('rep'):
                continue
            try:
                q = ExamQuestion.objects.get(id=quest.replace('rep',''))
            except ExamQuestion.DoesNotExist:
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
            self.score = round(float(self.total)/self.max*100)
        except ZeroDivisionError:
            self.score = 0
        try:
            cas = q.examen
        except UnboundLocalError:
            return HttpResponseRedirect('/')
        self.titre = cas.titre
        r = ExamScore(utilisateur=self.user, examen=cas.examen, score=self.score)
        r.save()
        self.enonces = enonces.values()
        return
