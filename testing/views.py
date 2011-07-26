# -*- encoding: utf-8 -*-

import os.path

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site
from django.contrib.auth.decorators import login_required
from django.template import RequestContext, loader
from django.template.defaulttags import include_is_allowed
from django.conf import settings

from testing.models import Granule, ExamCas
from testing.controllers import UserTest, UserSubmittedTest
from testing.controllers import UserExam, UserCase, UserSubmittedCase
from learning.controllers import UserModule

LOGIN_REDIRECT_URL = getattr(settings, 'LOGIN_REDIRECT_URL', '/')

@login_required
def test(request, granule_id=None):
    """
    Crée et affiche un test pour une granule donnée
    """
    if not granule_id:
        request.user.message_set.create(
                message=_("Requested url is invalid."))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    langue = request.GET.get('l',request.session['django_language'])
    try:
        granule = Granule.objects.get(pk=granule_id)
    except Granule.DoesNotExist:
        request.user.message_set.create(
                message=_("Requested test does not exist"))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    if not UserModule(request.user, granule.module).is_open():
        request.user.message_set.create(
                message=_("Requested test is not allowed."))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    site_id = getattr(settings, 'SITE_ID', 1)
    site = Site.objects.get(id=site_id)
    base = ''.join(('http://', site.domain))
    contents_prefix = getattr(settings, 'CONTENTS_PREFIX', 'contents')
    suffixe = os.path.join( contents_prefix,
                            granule.module.slug,
                            'imgtests/')
    base = os.path.join(base, suffixe)

    if request.method == 'POST':
        test = UserSubmittedTest(request)
        test.noter()
        return render_to_response('testing/noter.html',{
                                    'title' : _("grade"),
                                    'test' : test,
                                    'baselink' : base,
                                    }, context_instance=RequestContext(request))

    test = UserTest(request.user, granule, langue)
    t = loader.get_template('testing/test.html')
    c = RequestContext(request,{
                'title' : _("test"),
                'test' : test,
                'baselink' : base,})
    response = HttpResponse(t.render(c))
    response['Cache-Control'] = 'no-cache, no-store'
    return response

def cas(request, cas_id=None):
    """
    Choisit et affiche un cas
    """
    if not cas_id:
        request.user.message_set.create(
                message=_("Requested url is invalid."))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    try:
        cas = ExamCas.objects.get(pk=cas_id)
    except ExamCas.DoesNotExist:
        request.user.message_set.create(
                message=_("Requested test does not exist"))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    if not UserExam(request.user, cas.examen).is_open():
        request.user.message_set.create(
                message=_("Requested exam is closed."))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    site_id = getattr(settings, 'SITE_ID', 1)
    site = Site.objects.get(id=site_id)
    base = ''.join(('http://', site.domain))
    contents_prefix = getattr(settings, 'CONTENTS_PREFIX', 'contents')
    suffixe = os.path.join(contents_prefix, 'cas', cas.slug, cas.ressource)
    base = os.path.join(base, suffixe)
    support_path = os.path.join(settings.PROJECT_PATH, suffixe)
    if not include_is_allowed(support_path):
        request.user.message_set.create(
                message=_("You are not allowed to browse the requested content."))
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    if request.method == 'POST':
        exam = UserSubmittedCase(request)
        exam.noter()
        if cas.examen.display_note:
            return render_to_response('testing/noter_cas.html',{
                                        'title' : _("grade"),
                                        'exam' : exam,
                                        'baselink' : base,
                                        }, context_instance=RequestContext(request))
        else:
            request.user.message_set.create(
                    message=_("Your answers have been saved."))
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    try:
        cas.texte = open(support_path).read()
    except IOError:
        if settings.DEBUG:
            cas.texte = "Unable to open file %s" % support_path
        else:
            cas.texte = "<!-- Unable to open file %s -->\n" % support_path
    cas = UserCase(request.user, cas)
    return render_to_response('testing/cas.html',{
                                'title': cas.titre,
                                'baselink': base,
                                'breadcrumb': cas.titre,
                                'cas' : cas,
                                }, context_instance=RequestContext(request))

