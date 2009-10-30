# -*- encoding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template import RequestContext
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings

from coaching.models import Utilisateur, Groupe
from coaching.forms import UtilisateurChangeForm, CreateLoginsForm
from coaching.controllers import AdminGroupe

LOGIN_REDIRECT_URL = getattr(settings, 'LOGIN_REDIRECT_URL', '/')

@login_required
def profile(request):
    """
    Modifier le compte Utilisateur.
    Les champs que l'Utilisateur peut changer sont :
    - email
    - password
    - langue
    """
    if request.method == "POST":
        form = UtilisateurChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            request.session['django_language'] = request.user.langue
            request.user.message_set.create(
                    message=_("Changes saved successfully."))
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
        else:
            return render_to_response('coaching/change_profile.html', {
                'form': form,
            }, context_instance=RequestContext(request))
    else:
        form = UtilisateurChangeForm(instance=request.user)
    return render_to_response('coaching/change_profile.html', {
        'title': _('Change account'),
        'form': form,
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
    if request.user.id != groupe.administrateur.id:
        request.user.message_set.create(
                message=_("You do not have admin rights on the requested group."))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    groupe = AdminGroupe(request.user, groupe)
    return render_to_response('coaching/groupe.html',
                              {'title': _('Group students'),
                               'groupe': groupe,
                              },
                              context_instance=RequestContext(request))

@login_required
def user(request, user_id):
    """
    Fiche récapitulative des performances d'un utilisateur
    """
    return render_to_response('coaching/user.html',
                              {'title': _('User'),
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
