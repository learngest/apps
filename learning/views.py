# -*- encoding: utf-8 -*-

#import os
import sys
import os.path
import datetime

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template import RequestContext
from django.conf import settings
from django.contrib.sites.models import Site
from django.template.defaulttags import include_is_allowed

from learning.models import Cours, Module, Contenu, ModuleTitre
from coaching.models import Work, WorkDone, Groupe
from testing.models import Granule, Question
from coaching.forms import WorkForm
from learning.controllers import UserCours, UserModule

LOGIN_REDIRECT_URL = getattr(settings, 'LOGIN_REDIRECT_URL', '/')

@login_required
def support(request, contenu_id=None):
    """
    Display course content.
    """
    if not contenu_id:
        request.user.message_set.create(
                message=_("Requested url is invalid."))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    langue = request.GET.get('l',request.session['django_language'])
    try:
        contenu = Contenu.objects.get(pk=contenu_id)
    except Contenu.DoesNotExist:
        request.user.message_set.create(
                message=_("Requested content does not exist"))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    if not UserModule(request.user, contenu.module).is_open():
        request.user.message_set.create(
                message=_("Requested content is not allowed."))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    if langue != contenu.langue:
        try:
            contenu = Contenu.objects.get(module=contenu.module,
                                          type=contenu.type,
                                          langue=contenu.langue)
        except Contenu.DoesNotExist:
            request.user.message_set.create(
                message=_("Sorry, this content is not available in your prefered language."))
    site_id = getattr(settings, 'SITE_ID', 1)
    site = Site.objects.get(id=site_id)
    base = ''.join(('http://', site.domain))
    contents_prefix = getattr(settings, 'CONTENTS_PREFIX', 'contents')
    curmod = sys.modules['learning.views']
    fonction = 'render_%s' % contenu.type
    return getattr(curmod, 
            fonction, render_any)(request, contenu, base, contents_prefix)
    
def render_htm(request, c, base, contents_prefix):
    """
    Render html support
    """
    suffixe = os.path.join( contents_prefix,
                            c.module.slug,
                            c.langue,
                            c.ressource)
    support_path = os.path.join(settings.PROJECT_PATH, suffixe)
    base = os.path.join(base, suffixe)
    if not include_is_allowed(support_path):
        request.user.message_set.create(
                message=_("You are not allowed to browse the requested content."))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    try:
        support = open(support_path).read()
    except IOError:
        if settings.DEBUG:
            support = "Unable to open file %s" % support_path
        else:
            support = "<!-- Unable to open file %s -->\n" % support_path
    return render_to_response('learning/html_support.html',{
                                'title': c.titre,
                                'baselink': base,
                                'breadcrumb': c.module.titre(c.langue),
                                'support' : support,
                                }, context_instance=RequestContext(request))

def render_swf(request, c, base, contents_prefix):
    """
    Render swf (flash) support
    """
    suffixe = os.path.join( contents_prefix,
                            c.module.slug,
                            c.langue,
                            'flash',
                            c.ressource)
    support_path = os.path.join(settings.PROJECT_PATH, suffixe)
    base = os.path.join(base, suffixe)
    if not include_is_allowed(support_path):
        request.user.message_set.create(
                message=_("You are not allowed to browse the requested content."))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    return render_to_response('learning/swf_support.html',{
                                'title': c.titre,
                                'baselink': base,
                                'contents_prefix': contents_prefix,
                                'breadcrumb': c.module.titre(c.langue),
                                'support' : suffixe,
                                }, context_instance=RequestContext(request))

def render_any(request, c, base, contents_prefix):
    return HttpResponseRedirect("/%s/%s/%s/autres/%s" %
                    (contents_prefix,c.module.slug, c.langue, c.ressource))

@login_required
def tabcours(request):
    """
    Tableau de l'ensemble des cours
    """
    cours = [UserCours(request.user, cours) 
            for cours in request.user.groupe.cours.order_by('coursdugroupe__rang')]
    return render_to_response('learning/liste_cours.html',{
                                'title' : _("courses list"),
                                'cours' : cours,
                                }, context_instance=RequestContext(request))

@login_required
def assignment(request, work_id=None):
    """
    Display assignment and allow to upload it.
    """
    if not work_id:
        request.user.message_set.create(
                message=_("Requested url is invalid."))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    try:
        work = Work.objects.get(pk=work_id)
    except Work.DoesNotExist:
        request.user.message_set.create(
                message=_("Requested assignment does not exist"))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    if not UserCours(request.user, work.cours).is_open():
        request.user.message_set.create(
                message=_("Requested assignment is not allowed"))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    if work.fichier.path:
        work.fname = os.path.basename(work.fichier.path)
    if request.method == 'POST':
        f = WorkForm(request.POST, request.FILES)
        if f.is_valid():
            if f.cleaned_data['fichier']:
                import sha
                import zipfile
                fichier = ''.join(('g%d-' % request.user.groupe.id,
                            request.user.username,'-',
                            datetime.datetime.now().strftime('%Y%m%d-%H%M%S'),
                            os.path.splitext(f.cleaned_data['fichier'].name)[1]))
                fichier = fichier.encode('iso-8859-1')
                content = request.FILES['fichier']
                signature = sha.new(content.read()).hexdigest()
                date = datetime.datetime.now()
                # try: si le devoir existe, pas de sauvegarde.
                try:
                    wd = WorkDone.objects.get(utilisateur=request.user, work=work)
                except WorkDone.DoesNotExist:
                    wd = WorkDone(
                            utilisateur=request.user, 
                            work=work, 
                            date=date, 
                            fichier=fichier, 
                            signature=signature)
                    wd.fichier.save(fichier, content, save=True)
                    # groupe-cours zipfile
                    zfichier = 'g%d-%s.zip' % (request.user.groupe.id,
                            work.cours.slug)
                    try:
                        zf = zipfile.ZipFile(
                            os.path.join(settings.MEDIA_ROOT,
                                        settings.WORKDONE_DIR,zfichier),
                                        'a',zipfile.ZIP_DEFLATED)
                    except IOError:
                        zf = zipfile.ZipFile(
                            os.path.join(settings.MEDIA_ROOT,
                                        settings.WORKDONE_DIR,zfichier),
                                        'w',zipfile.ZIP_DEFLATED)
                    zf.write(os.path.join(settings.MEDIA_ROOT,
                                    settings.WORKDONE_DIR,fichier))
                    zf.close()
                    # login zipfile
                    zfichier = ''.join(('g%d' % request.user.groupe.id,'-', 
                                        request.user.username,
                                        '.zip'))
                    try:
                        zf = zipfile.ZipFile(
                            os.path.join(settings.MEDIA_ROOT,
                                        settings.WORKDONE_DIR,zfichier),
                                        'a',zipfile.ZIP_DEFLATED)
                    except IOError:
                        zf = zipfile.ZipFile(
                            os.path.join(settings.MEDIA_ROOT,
                                        settings.WORKDONE_DIR,zfichier),
                                        'w',zipfile.ZIP_DEFLATED)
                    zf.write(os.path.join(settings.MEDIA_ROOT,
                            settings.WORKDONE_DIR,fichier))
                    zf.close()
                    request.user.nb_travaux_rendus += 1
                    # cours validé ?
                    uc = UserCours(request.user, request.user.current)
                    if uc.valide:
                        request.user.nb_cours_valides += 1
                        # nouveau cours, raz nb_modules et nb_valides
                        request.user.nb_modules = None
                        request.user.nb_valides = 0
                        try:
                            request.user.current = uc.liste_cours[uc.rang+1]
                        except IndexError:
                            pass
                    request.user.save()
                    return render_to_response('learning/assignment.html',{
                             'work': work,
                             'fichier': fichier,
                             'signature': signature,
                             }, context_instance=RequestContext(request))
        return render_to_response('learning/assignment.html',{
                    'form': f,
                    'work': work,
                    }, context_instance=RequestContext(request)) 
    else:
        f = WorkForm()
        return render_to_response('learning/assignment.html',{
                                    'form': f,
                                    'work': work,
                                    }, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_staff)
def stats(request, langue='fr'):
    try:
        template = Groupe.objects.get(nom='template-%s' % langue)
        cours = template.cours.order_by('coursdugroupe__rang')
    except Groupe.DoesNotExist:
        cours = Cours.objects.all()
    for c in cours:
        c.title = c.titre(langue)
        c.modules = c.liste_modules()
        for m in c.modules:
            m.title = m.titre(langue)
            m.contents = Contenu.objects.filter(
                module=m,
                langue=langue)
            m.htm = m.contents.filter(type='htm')
            m.swf = m.contents.filter(type='swf')
            m.pdf = m.contents.filter(type='pdf')
            m.granules = Granule.objects.filter(module=m)
            for g in m.granules:
                g.title = g.titre(langue)
                g.tests = Question.objects.filter(
                        granule=g,
                        langue=langue).count()
            else:
                if not m.granules:
                    g = Granule(slug='empty',
                                module = m,
                                nbq = 0,
                                score_min = 0,
                                rang = 10)
                    g.title = '--'
                    g.tests = 0
                    m.granules = [g]
    return render_to_response('learning/stats.html',{
                                'cours': cours,
                                }, context_instance=RequestContext(request))
