# -*- encoding: utf-8 -*-

import sys

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required

from dashboard.planning import Calendrier, Planning

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

    return render_to_response('dashboard/etudiant.html',
                              {'title': _('dashboard'),
                               'cal': cal,
                               'planning': planning,
                              },
                              context_instance=RequestContext(request))

def dashboard_staff(request):
    """
    Tableau de bord staff, lien vers l'admin
    """
    return HttpResponseRedirect("/staff/")
