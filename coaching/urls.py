# -*- encoding: utf-8 -*-

from django.conf.urls.defaults import *

urlpatterns = patterns('coaching.views',
    (r'^groupe/(?P<groupe_id>\d+)/$', 'groupe',),
    (r'^cours/(?P<gcp_id>\d+)/$', 'cours',),
    (r'^user/(?P<user_id>\d+)/$', 'user',),
    (r'^sendmail/$', 'sendmail',),
    (r'^upload/$', 'add_doc',),
    (r'^csv/$', 'csvperf',),
)
