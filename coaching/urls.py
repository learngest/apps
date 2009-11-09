# -*- encoding: utf-8 -*-

from django.conf.urls.defaults import *

urlpatterns = patterns('coaching.views',
    (r'^groupe/(?P<groupe_id>\d+)/$', 'groupe',),
    #url(r'^groupe/(?P<groupe_id>\d+)/$', 'groupe', name='group_view'),
    (r'^user/(?P<user_id>\d+)/$', 'user',),
)
