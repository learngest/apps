# -*- encoding: utf-8 -*-

from django.conf.urls.defaults import *

urlpatterns = patterns('learning.views',
#    (r'^common/(?P<slug>[a-z0-9-]+)/$', 'lg.learning.views.help_support'),
#    (r'^support/(?P<slug>[a-z0-9-]+)/$', 'lg.learning.views.support', {'ltyp': 'htm'}),
#    (r'^anim/(?P<slug>[a-z0-9-]+)/$', 'lg.learning.views.support', {'ltyp': 'swf'}),
    (r'^contents/(?P<contenu_id>\d+)/$', 'support',),
    (r'^assignments/(?P<work_id>\d+)/$', 'assignment',),
    (r'^courses/$', 'tabcours',),
)
