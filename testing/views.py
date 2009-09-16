# -*- encoding: utf-8 -*-

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.conf import settings

from testing.models import Granule
from testing.controllers import UserTest

@login_required
def test(request, granule_id=None):
    """
    Crée et affiche un test pour une granule donnée
    """
    if request.method == 'POST':
        test = UserSubmittedTest(request.user, request.POST.lists())
        test.noter()
        return render_to_response('testing/test.html',{
                                    'title' : _("grade"),
                                    'test' : test,
                                    }, context_instance=RequestContext(request))
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
    test = UserTest(request.user, granule, langue)
    return render_to_response('testing/test.html',{
                                'title' : _("test"),
                                'test' : test,
                                }, context_instance=RequestContext(request))

