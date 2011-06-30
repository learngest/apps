# -*- encoding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import activate, ugettext as _
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template import RequestContext
from django.template.loader import render_to_string
from django.template.defaultfilters import slugify
from django.core import urlresolvers
from django.core.mail import send_mail, EmailMessage
from django.conf import settings

from coaching.models import Utilisateur, Groupe, Prof, AutresDocs
from coaching.forms import UtilisateurChangeForm, CreateLoginsForm, MailForm, DocumentForm
from coaching.controllers import AdminGroupe, UserState, ProfCours, filters, AdminCours
from dashboard.planning import Calendrier, Planning
from testing.models import Examen

from listes import *

LOGIN_REDIRECT_URL = getattr(settings, 'LOGIN_REDIRECT_URL', '/')

@login_required
def profile(request):
    """
    Modifier le compte Utilisateur.
    Les champs que l'Utilisateur peut changer sont :
    - password
    - langue
    """
    if request.method == "POST":
        form = UtilisateurChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            request.session['django_language'] = request.user.langue
            activate(request.user.langue)
            request.user.message_set.create(
                    message=_("Changes saved successfully."))
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
        else:
            return render_to_response('coaching/change_profile.html', {
                'form': form,
                'here':'profile',
            }, context_instance=RequestContext(request))
    else:
        form = UtilisateurChangeForm(instance=request.user)
    return render_to_response('coaching/change_profile.html', {
        'title': _('Change account'),
        'form': form,
        'here':'profile',
    }, context_instance=RequestContext(request))
    
@login_required
def groupe(request, groupe_id):
    """
    Voir les logins d'un groupe et le travail accompli
    """
    try:
        groupe = Groupe.objects.get(id=groupe_id)
    except Groupe.DoesNotExist:
        request.user.message_set.create(
                message=_("This group does not exist."))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    if not request.user.may_see_groupe(groupe):
            request.user.message_set.create(
                    message=_(
                        "You do not have admin rights on the requested group."))
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    groupe_complet = AdminGroupe(request.user, groupe)
    filtdict = {}
    filtraw = ''
    if request.method == 'POST':
        if 'filter' in request.POST:
            if request.POST['filter']:
                filtraw = request.POST['filter']
                for f in filtraw.split('&'):
                    key, value = f.split('=')
                    filtdict[str(key)] = int(value)
            filtres = filters(request.user, groupe_complet, filtraw)
            groupe = AdminGroupe(request.user, groupe, filtdict)
    else:
        filtres = filters(request.user, groupe_complet)
        groupe = groupe_complet
    actions = [{'libel':_('Download group results'),
                'url':'%s?id=%s' % (
                    urlresolvers.reverse('coaching.views.csvperf'),
                    groupe_id)},
            {'libel':_('See group planning and courses'),
             'url': '%s?id=%s' % (
                urlresolvers.reverse('coaching.views.dashboard'),
                groupe_id)},]
    actions_admin = [
            {'libel':_('Upload a file for this group'),
             'url':'%s?id=%s' % (
                 urlresolvers.reverse('coaching.views.add_doc'),
                 groupe_id)},
            {'libel':_('Send an email to selected students'),
             'url': '%s?id=%s&%s' % (
                urlresolvers.reverse('coaching.views.sendmail'),
                groupe_id, filtraw)},]
    actions_staff = [
            {'libel':_('Group admin'),
             'url': groupe.get_admin_url},]
    if request.user.statut > PROF:
        actions.extend(actions_admin)
        if request.user.statut == STAFF:
            actions.extend(actions_staff)
    return render_to_response('coaching/groupe.html',
                              {'title': groupe.nom,
                               'actions': actions,
                               'groupe': groupe,
                               'filters': filtres,
                              },
                              context_instance=RequestContext(request))

@login_required
def examresults(request, exam_id=None):
    """
    Affiche les résultats à un examen
    """
    try:
        examen = Examen.objects.get(id=exam_id)
    except Examen.DoesNotExist:
        request.user.message_set.create(
                message=_("This exam does not exist."))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    if not request.user.may_see_groupe(examen.groupe):
            request.user.message_set.create(
                    message=_(
                        "You do not have admin rights on the requested group."))
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    groupe = AdminGroupe(request.user, examen.groupe)
    for user in groupe.users():
        user.score = user.resultat(examen)
    actions = [{'libel':_('Download group results'),
                'url':'%s?id=%s' % (
                    urlresolvers.reverse('coaching.views.csvperf'),
                    examen.groupe_id)},]
    return render_to_response('coaching/resultats.html',
                              {'title': examen.titre,
                               'actions': actions,
                               'groupe': groupe,
                              },
                              context_instance=RequestContext(request))

@login_required
def dashboard(request):
    """
    Voir le tableau de bord et le planning d'un groupe
    """
    if 'id' in request.GET:
        try:
            groupe = Groupe.objects.get(id=request.GET['id'])
        except Groupe.DoesNotExist:
            request.user.message_set.create(
                    message=_("This group does not exist."))
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
        if not request.user.may_see_groupe(groupe):
            request.user.message_set.create(
                message=_(
                    "You do not have admin rights on the requested group."))
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    else:
        request.user.message_set.create(
                message=_("This group does not exist."))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)

    cal = Calendrier(request, groupe)
    planning = Planning(request, groupe)
    docs = AutresDocs.objects.filter(groupe=groupe,cours=None)
    cours = [AdminCours(request.user, cours, groupe) for cours
            in groupe.cours.order_by('coursdugroupe__rang')]
    exams = Examen.objects.filter(groupe=groupe)

    return render_to_response('coaching/group_dashboard.html',
                              {'title': groupe.nom,
                               'groupe': groupe,
                               'cal': cal,
                               'planning': planning,
                               'docs': docs,
                               'cours' : cours,
                               'exams' : exams,
                              },
                              context_instance=RequestContext(request))


@login_required
def csvperf(request):
    """
    Download group performances as .csv file
    """
    import csv
    from django.template.defaultfilters import slugify
    if 'id' in request.GET:
        try:
            groupe = Groupe.objects.get(id=request.GET['id'])
        except Groupe.DoesNotExist:
            request.user.message_set.create(
                    message=_("This group does not exist."))
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
        if not request.user.may_see_groupe(groupe):
            request.user.message_set.create(
                message=_(
                    "You do not have admin rights on the requested group."))
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = \
            'attachment; filename=groupe-%s.csv' % slugify(groupe.nom)
    examens = Examen.objects.filter(groupe=groupe)
    writer = csv.writer(response,delimiter=';')
    groupe = AdminGroupe(request.user, groupe)
    headers = [ _('Last Name'),
            _('First Name'),
            _('Email'),
            _('Last login'),
            _('Valid till'),
            _('Completed courses / %d') % groupe.nb_cours,
            _('Uploaded works / %d') % groupe.nb_works,
            _('Current course'),
            _('Validated modules in current course'),
            _('# modules in current course'),
            _('Delays'),]
    headers.extend([exam.titre for exam in examens])
    writer.writerow([s.encode("utf-8") for s in headers])
    for u in groupe.users():
        line = [
            u.user.last_name.encode("utf-8"),
            u.user.first_name.encode("utf-8"),
            u.email.encode("utf-8"),
            u.last_login,
            u.user.fermeture,
            u.nb_cours_valides(),
            u.nb_travaux_rendus(),
            u.cours_courant().titre().encode("utf-8"),
            u.nb_modules_valides_in_current(),
            u.nb_modules_in_current(),
            u.nb_cours_en_retard(),
            ]
        line.extend([u.resultat(exam) for exam in examens])
        writer.writerow(line)
    return response

@login_required
def add_doc(request):
    """
    Dépôt de document pour un groupe
    """
    if 'id' in request.GET:
        try:
            groupe = Groupe.objects.get(id=request.GET['id'])
        except Groupe.DoesNotExist:
            request.user.message_set.create(
                    message=_("This group does not exist."))
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
        if not request.user.may_admin_groupe(groupe):
            request.user.message_set.create(
                message=_(
                    "You do not have admin rights on the requested group."))
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    if request.method != 'POST':
        f = DocumentForm()
        return render_to_response('coaching/upload.html',
                            {'title': _('Upload a file for %s') % groupe.nom,
                             'groupe': groupe,
                             'form': f,
                            },
                          context_instance=RequestContext(request))
    else:
        f = DocumentForm(request.POST, request.FILES)
        if f.is_valid():
            fichier = request.FILES['fichier']
            filename, extension = fichier.name.rsplit('.',1)
            filename = '.'.join((slugify(filename), extension))
            doc = AutresDocs(
                    groupe=groupe,
                    cours=f.cleaned_data['cours'],
                    titre=f.cleaned_data['titre'],
                    fichier=filename)
            doc.fichier.save(filename, fichier, save=True)
            request.user.message_set.create(
                    message=_("The document has been uploaded correctly."))
            return HttpResponseRedirect(groupe.get_absolute_url())
        else:
            return render_to_response('coaching/upload.html',
                            {'title': _('Upload a file for %s') % groupe.nom,
                             'groupe': groupe,
                             'form': f,
                            },
                          context_instance=RequestContext(request))

@login_required
def sendmail(request):
    """
    Send an email to selected users
    """
    if 'id' in request.GET:
        try:
            groupe = Groupe.objects.get(id=request.GET['id'])
        except Groupe.DoesNotExist:
            request.user.message_set.create(
                    message=_("This group does not exist."))
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
        if not request.user.may_admin_groupe(groupe):
            request.user.message_set.create(
                message=_(
                    "You do not have admin rights on the requested group."))
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
        destinataires = Utilisateur.objects.filter(groupe=groupe)
        filtdict = {}
        for key,value in request.GET.items():
            if key != 'id':
                filtdict.update({str(key): int(value)})
        destinataires = destinataires.filter(**filtdict)
        dest_list = [u.get_full_name() for u in destinataires]
        email_list = [u.email for u in destinataires]
        utilisateur = None
    if 'uid' in request.GET:
        try:
            utilisateur = Utilisateur.objects.get(id=request.GET['uid'])
        except Utilisateur.DoesNotExist:
            request.user.message_set.create(
                    message=_("This user does not exist."))
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
        if not request.user.may_admin_groupe(utilisateur.groupe):
            request.user.message_set.create(
                message=_(
                    "You do not have admin rights on the requested group."))
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
        dest_list = [utilisateur.get_full_name()]
        email_list = [utilisateur.email]
        groupe = utilisateur.groupe
    if request.method != 'POST':
        f = MailForm()
        return render_to_response('coaching/sendmail.html',
                            {'title': _('Send an email'),
                             'groupe': groupe,
                             'utilisateur': utilisateur,
                             'dest_list': dest_list,
                             'form': f,
                            },
                          context_instance=RequestContext(request))
    if request.method == 'POST':
        f = MailForm(request.POST)
        if f.is_valid():
            email_list.append(request.user.email)
            subject = f.cleaned_data['subject']
            message = f.cleaned_data['content']
            from_email = '%s <profs@learngest.com>' % request.user.get_full_name()
            reply_to = request.user.email
            attach = None
            if 'attach' in request.FILES:
                attach = request.FILES['attach']
            try:
                mail = EmailMessage(subject=subject,
                        body=message,
                        from_email=from_email,
                        to=email_list,
                        headers={'Reply-To': reply_to})
                if attach:
                    mail.attach(attach.name, attach.read(), attach.content_type)
                mail.send()
                request.user.message_set.create(
                        message=_("The message has been sent."))
            except:
                request.user.message_set.create(
                        message=_("Error: unable to send message."))
            if utilisateur:
                return HttpResponseRedirect(utilisateur.get_absolute_url())
            else:
                return HttpResponseRedirect(groupe.get_absolute_url())
        else:
            return render_to_response('coaching/sendmail.html',
                                {'title': _('Send an email'),
                                 'groupe': groupe,
                                 'dest_list': dest_list,
                                 'form': f,
                                },
                              context_instance=RequestContext(request))

@login_required
def cours(request, gcp_id):
    """
    Voir les résultats d'un groupe pour un seul cours
    """
    try:
        gcp = Prof.objects.get(id=gcp_id)
    except Prof.DoesNotExist:
        request.user.message_set.create(
            message=_("You do not have professor rights on the requested group."))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    if not request.user == gcp.utilisateur:
        request.user.message_set.create(
            message=_("You do not have professor rights on the requested group."))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    cours = ProfCours(request.user, gcp)
    return render_to_response('coaching/cours.html',
                              {'title': gcp.groupe.nom,
                               'cours': cours,
                              },
                              context_instance=RequestContext(request))

@login_required
def user(request, user_id):
    """
    Fiche récapitulative des performances d'un utilisateur
    """
    try:
        utilisateur = Utilisateur.objects.get(id=user_id)
    except Utilisateur.DoesNotExist:
        request.user.message_set.create(
                message=_("This user does not exist."))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    if not request.user.may_see_groupe(utilisateur.groupe):
            request.user.message_set.create(
                    message=_(
                        "You do not have admin rights on the requested group."))
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    us = UserState(utilisateur)
    exams = us.exams()
    actions = []
    actions_admin = [
            {'libel':_('Send an email to this student'),
             'url': '%s?uid=%s' % (
                urlresolvers.reverse('coaching.views.sendmail'),
                utilisateur.id)},]
    actions_staff = [
            {'libel':_('User admin'),
             'url': utilisateur.get_admin_url()},]
    if request.user.statut > PROF:
        actions.extend(actions_admin)
        if request.user.statut == STAFF:
            actions.extend(actions_staff)
    return render_to_response('coaching/user.html',
                              {'title': us.get_full_name,
                               'student': us,
                               'actions': actions,
                               'exams': exams,
                              },
                              context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_staff)
def create_logins(request):
    """
    Création de logins à partir d'un fichier
    """
    import os
    import time
    import StringIO
    import random
    import sha
    if request.method == 'POST':
        if 'fsource' in request.POST:
            fsource = os.path.join(settings.MEDIA_ROOT,'logins',
                    request.POST['fsource'])
            g = Groupe.objects.get(id=request.POST['groupe'])
            logins = []
            nom_logins = 'logins-g%s-%s.txt'% (g.id, 
                        time.strftime('%Y%m%d%H%M%S',time.localtime()))
            fich_logins = os.path.join(settings.MEDIA_ROOT,'logins',nom_logins)
            url_logins = os.path.join(settings.MEDIA_URL,'logins',nom_logins)
            flogin = open(fich_logins,'w')
            newline = ';'.join(('Last name','First name','Email','Password','\n'))
            flogin.write(newline)
            for line in open(fsource):
                line = line.strip()
                line = line.decode('iso-8859-1')
                nom, prenom, email = line.split('\t')
                nom = nom.strip().title()
                prenom = prenom.strip().title()
                username = email.split('@')[0][:30]
#                login = unicodedata.normalize('NFKD',login).encode('ASCII',
#                        'ignore').lower()
#                login = login.replace(' ','')
                password = sha.new(str(random.random())).hexdigest()[:8]
                try:
                    Utilisateur.objects.get(email=email)
                    saved = False
                    status = _('Exists already.')
                except Utilisateur.DoesNotExist:
                    u = Utilisateur(username=username, last_name=nom, 
                                    first_name=prenom, 
                                    email=email, 
                                    fermeture=request.POST['fermeture'], 
                                    langue=request.POST['langue'], groupe=g)
                    u.set_password(password)
                    u.save()
                    saved = True
                    status = _('Saved.')
                if request.POST['envoi_mail']=='1' and saved:
                    try:
                        mailmsg = render_to_string('coaching/mail_login.txt', 
                                {'login': u.email, 
                                  'password': password,
                                  'groupe': g.nom,
                                  'coach': g.administrateur.get_full_name(),
                                  'coach_mail': g.administrateur.email,})
                        send_mail(subject='E-learning - %s' % g.client.nom,
                                  message = mailmsg,
                                  from_email='info@learngest.com',
                                  recipient_list=[u.email],
                                  )
                        status = ' '.join((status,_('Mail sent.')))
                    except IOError:
                        status = ' '.join((status,_('Mail error.')))
                if saved:
                    newline = ';'.join((nom,prenom,email,password,'\n'))
                    newline = newline.encode('iso-8859-1')
                    flogin.write(newline)
                logins.append({'email':email, 'password': password, 
                                'nom':nom,'prenom':prenom,'status': status,
                                })
            flogin.close()
            return render_to_response('coaching/create_logins3.html',
                                {'title': _('Create logins'),
                                 'logins': logins,
                                 'groupe': g,
                                 'langue': request.POST['langue'],
                                 'fermeture': request.POST['fermeture'],
                                 'envoi_mail': int(request.POST['envoi_mail']),
                                 'fsource': nom_logins,
                                 'usource': url_logins,
                                },
                                context_instance=RequestContext(request))
        else:
            f = CreateLoginsForm(request.POST, request.FILES)
            f.fields['groupe'].choices = [(g.id, g.nom) 
                    for g in Groupe.objects.order_by('nom')]
            if f.is_valid():
                g = Groupe.objects.get(id=f.cleaned_data['groupe'])
                start_now = False
                logins = []
                nom_source = "source-g%s-%s.txt" % (g.id, 
                        time.strftime('%Y%m%d%H%M%S',time.localtime()))
                fich_source = os.path.join(settings.MEDIA_ROOT, 'logins', 
                        nom_source)
                fsource = open(fich_source, 'w')
                for line in StringIO.StringIO(request.FILES['source'].read()):
                    if line.startswith('Nom\t'):
                        start_now = True
                        continue
                    if start_now:
                        line = line.decode('iso-8859-1').strip()
                        if not line:
                            continue
                        try:
                            nom, prenom, email = line.split('\t')
                        except ValueError:
                            request.user.message_set.create(
                                    message=_("Invalid file content : %s") % line)
                            fsource.close()
                            os.unlink(fich_source)
                            return render_to_response('coaching/create_logins.html',
                                          {'title': _('Create logins'),
                                           'form': f,
                                          },
                                          context_instance=RequestContext(request))
                        nom = nom.strip().title()
                        prenom = prenom.strip().title()
                        email = email.strip().lower()
                        logins.append({'nom':nom,'prenom':prenom,'email':email})
                        line = line.encode('iso-8859-1')
                        fsource.write(line)
                        fsource.write('\n')
                fsource.close()
                return render_to_response('coaching/create_logins2.html',
                                    {'title': _('Create logins'),
                                     'logins': logins,
                                     'groupe': g,
                                     'langue': f.cleaned_data['langue'],
                                     'fermeture': f.cleaned_data['fermeture'],
                                     'envoi_mail': int(f.cleaned_data['envoi_mail']),
                                     'fsource': nom_source,
                                    },
                                    context_instance=RequestContext(request))
            else:
                return render_to_response('coaching/create_logins.html',
                                  {'title': _('Create logins'),
                                   'form': f,
                                  },
                                  context_instance=RequestContext(request))
    else:
        f = CreateLoginsForm()
        f.fields['groupe'].choices = [(g.id, g.nom) 
                    for g in Groupe.objects.order_by('nom')]
        return render_to_response('coaching/create_logins.html',
                                  {'title': _('Create logins'),
                                   'form': f,
                                  },
                                  context_instance=RequestContext(request))
