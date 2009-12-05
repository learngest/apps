# -*- encoding: utf-8 -*-

import sys

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.core import urlresolvers

from dashboard.planning import Calendrier, Planning
from learning.controllers import UserCours
from coaching.controllers import AdminGroupe, UserState
from coaching.models import Groupe, Prof, AutresDocs

@login_required
def dashboard(request):
    """
    Wrapper pour les tableaux de bords des différents types
    d'utilisateurs :
    - staff
    - admin
    - prof
    - assistant
    - etudiant
    """
    curmod = sys.modules['dashboard.views']
    fonction = "dashboard_%s" % request.user.get_statut_display()
    return getattr(curmod, 
            fonction, dashboard_student)(request)

def dashboard_student(request):
    """
    Tableau de bord étudiant
    """
    cal = Calendrier(request)
    planning = Planning(request)
    us = UserState(request.user)
    course = us.cours_courant(recalcul=True)
    #course = UserCours(request.user, request.user.current)
    docs = AutresDocs.objects.filter(groupe=request.user.groupe,cours=None)


    return render_to_response('dashboard/etudiant.html',
                              {'title': _('dashboard'),
                               'cal': cal,
                               'planning': planning,
                               'course': course,
                               'docs': docs,
                              },
                              context_instance=RequestContext(request))

def dashboard_admin(request):
    """
    Tableau de bord administrateur
    """
    groupes = [AdminGroupe(request.user, groupe) 
            for groupe in Groupe.objects.filter(administrateur=request.user)]
    if len(groupes)==1:
        return HttpResponseRedirect(groupes[0].get_absolute_url)
    else:
        return render_to_response('dashboard/admin.html',
                                  {'title': _('dashboard'),
                                   'groupes': groupes,
                                  },
                                  context_instance=RequestContext(request))

def dashboard_prof(request):
    """
    Tableau de bord prof
    """
    cours = Prof.objects.filter(utilisateur=request.user)
    if len(cours)==1:
        return HttpResponseRedirect(cours[0].get_absolute_url())
    else:
        return render_to_response('dashboard/prof.html',
                                  {'title': _('dashboard'),
                                   'cours': cours,
                                  },
                                  context_instance=RequestContext(request))

def dashboard_assistant(request):
    """
    Tableau de bord assistant
    """
    groupes = [AdminGroupe(request.user, groupe)
            for groupe in Groupe.objects.filter(assistant=request.user)]
    if len(groupes)==1:
        return HttpResponseRedirect(groupes[0].get_absolute_url)
    else:
        return render_to_response('dashboard/admin.html',
                                  {'title': _('dashboard'),
                                   'groupes': groupes,
                                  },
                                  context_instance=RequestContext(request))

def dashboard_staff(request):
    """
    Tableau de bord staff
    """
    groupes = [AdminGroupe(request.user, groupe)
                for groupe in Groupe.objects.all()]
    if len(groupes)==1:
        return HttpResponseRedirect(groupes[0].get_absolute_url)
    else:
        return render_to_response('dashboard/admin.html',
                                  {'title': _('dashboard'),
                                   'groupes': groupes,
                                  },
                                  context_instance=RequestContext(request))
#    return HttpResponseRedirect(
#            urlresolvers.reverse('admin:coaching_utilisateur_changelist'))
