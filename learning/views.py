# -*- encoding: utf-8 -*-

#import os
import sys
import os.path
#import datetime

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.conf import settings
from django.contrib.sites.models import Site
from django.template.defaulttags import include_is_allowed

from learning.models import Cours, Module, Contenu, ModuleTitre

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

def render_any(request, c, base, contents_prefix):
    if not include_is_allowed(support_path):
        HttpResponseRedirect('/tdb/')
    try:
        support = open(support_path).read()
    except IOError:
        if settings.DEBUG:
            support = "Unable to open file %s" % support_path
        else:
            support = "<!-- Unable to open file %s -->\n" % support_path
    return render_to_response('learning/support.html',
                                {'visiteur': v.prenom_nom(),
                                 'client': v.groupe.client,
                                 'vgroupe': v.groupe,
                                 'admin': v.status,
                                 'baselink': base,
                                 'msg': msg,
                                 'support': support})

def render_swf(request, c, base, contents_prefix):
    support = os.path.join('/contents',c.module.slug,c.langue,'flash',c.ressource)
    base = os.path.join(base,'contents',c.module.slug,c.langue,'flash',c.ressource)
    return render_to_response('learning/anim.html',
                                {'visiteur': v.prenom_nom(),
                                 'client': v.groupe.client,
                                 'vgroupe': v.groupe,
                                 'admin': v.status,
                                 'baselink': base,
                                 'msg': msg,
                                 'support': support})

@login_required
def tabcours(request):
    """
    Tableau de l'ensemble des cours
    """
    return render_to_response('learning/liste_cours.html',{
                                'title' : _("courses list"),
                                'cours' : request.user.liste_cours_full(),
                                }, context_instance=RequestContext(request))

@login_required
def cours(request, course_id=None):
    """
    Détails d'un cours
    """
    return render_to_response('learning/liste_cours.html',{
                                'cours' : request.user.liste_cours(),
                                }, context_instance=RequestContext(request))
