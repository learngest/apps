# -*- encoding: utf-8 -*-

from django.conf.urls.defaults import *

urlpatterns = patterns('testing.views',
    (r'^cas/(?P<cas_id>\d+)/$', 'cas',),
    (r'^(?P<granule_id>\d+)/$', 'test',),
#    (r'^noter/$', 'noter',),
)
