# -*- encoding: utf-8 -*-

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required

from dashboard.planning import Calendrier

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
    return dashboard_etudiant(request)

def dashboard_etudiant(request):
    """
    Tableau de bord étudiant
    """
    cal = Calendrier(request)

    return render_to_response('dashboard/etudiant.html',
                              {'title': _('Dashboard'),
                               'cal': cal,},
                              context_instance=RequestContext(request))

