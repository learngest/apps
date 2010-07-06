# -*- encoding: utf-8 -*-

from django.conf.urls.defaults import *

urlpatterns = patterns('learning.views',
    url(r'^contents/(?P<contenu_id>\d+)/$', 'support', name='content_view'),
    url(r'^stats/(?P<langue>[a-zA-Z-]+)/$', 'stats', name='stats'),
    (r'^assignments/(?P<work_id>\d+)/$', 'assignment',),
    (r'^courses/$', 'tabcours',),
)
