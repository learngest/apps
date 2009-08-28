# -*- encoding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.conf import settings

from coaching.models import Utilisateur
from coaching.forms import UtilisateurChangeForm

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
                    message=_(u"Modifications enregistrées avec succès"))
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
        else:
            return render_to_response('coaching/change_profile.html', {
                'form': form,
            }, context_instance=RequestContext(request))
    else:
        form = UtilisateurChangeForm(instance=request.user)
    return render_to_response('coaching/change_profile.html', {
        'form': form,
    }, context_instance=RequestContext(request))
    
