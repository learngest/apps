# -*- encoding: utf-8 -*-

from django.conf.urls.defaults import *

urlpatterns = patterns('',
#    (r'^common/(?P<slug>[a-z0-9-]+)/$', 'lg.learning.views.help_support'),
#    (r'^support/(?P<slug>[a-z0-9-]+)/$', 'lg.learning.views.support', {'ltyp': 'htm'}),
#    (r'^anim/(?P<slug>[a-z0-9-]+)/$', 'lg.learning.views.support', {'ltyp': 'swf'}),
    (r'^contents/(?P<contenu_id>\d+)/$', 'learning.views.support',),
)
