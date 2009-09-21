# -*- encoding: utf-8 -*-

import sys

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required

from dashboard.planning import Calendrier, Planning
from learning.controllers import UserCours
from coaching.controllers import AdminGroupe
from coaching.models import Groupe

@login_required
def dashboard(request):
    """
    Wrapper pour les tableaux de bords des différents types
    d'utilisateurs :
    - staff
    - admin
    - prof
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
    course = UserCours(request.user,
            request.user.current or request.user.groupe.liste_cours()[0])


    return render_to_response('dashboard/etudiant.html',
                              {'title': _('dashboard'),
                               'cal': cal,
                               'planning': planning,
                               'course': course,
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

def dashboard_staff(request):
    """
    Tableau de bord staff, lien vers l'admin
    """
    return HttpResponseRedirect("/staff/")
