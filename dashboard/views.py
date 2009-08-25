# -*- encoding: utf-8 -*-

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required

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
    return render_to_response('base_site.html',
                              {'title': _('Dashboard')},
                              context_instance=RequestContext(request))
