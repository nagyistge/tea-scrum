'''
Created on 6 Jul 2012

@author: Ted
'''
from django.conf.urls.defaults import patterns, url
from views import taskboard, dailyscrum, submit_daily, pick_task, unpick_task, check_pick

urlpatterns = patterns('',
    url(r'^$', dailyscrum), #/daily
    url(r'^taskboard/?$', taskboard), #/daily/taskboard
    url(r'^submit/?$', submit_daily), #/daily/submit
    url(r'^pick/(?P<tid>\d*)$', pick_task), #/daily/pick/<tid>
    url(r'^unpick/(?P<tid>\d*)$', unpick_task), #/daily/unpick/<tid>
    url(r'^check/?$', check_pick), #/daily/check
)
