# -*- encoding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.conf import settings

from coaching.models import Utilisateur, Groupe
from coaching.forms import UtilisateurChangeForm
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
