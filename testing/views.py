# -*- encoding: utf-8 -*-

import os.path

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.conf import settings

from testing.models import Granule
from testing.controllers import UserTest, UserSubmittedTest
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
    return render_to_response('testing/test.html',{
                                'title' : _("test"),
                                'test' : test,
                                'baselink' : base,
                                }, context_instance=RequestContext(request))

