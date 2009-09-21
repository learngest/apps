# -*- encoding: utf-8 -*-

from django.conf.urls.defaults import *

urlpatterns = patterns('coaching.views',
    (r'^groupe/(?P<groupe_id>\d+)/$', 'groupe',),
    (r'^user/(?P<user_id>\d+)/$', 'user',),
)
