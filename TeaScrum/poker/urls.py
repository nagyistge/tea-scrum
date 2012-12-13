from django.conf.urls.defaults import patterns, url
from views import *

urlpatterns = patterns('',
    url(r'^start/$', start), #/poker/start/?pid=n, return {'sid':'xxx'}
    url(r'^stop/$', stop), #/poker/stop/?pid=n, return {"status":"OK"
    url(r'^status/$', status), #/poker/status/?pid=n, return {"status":"STARTED|CLOSED|IDLE"}
    url(r'^vote/$', vote), #/poker/vote/?pid=n&sid=xxx&vote=n, return {"status":"OK"}
    url(r'^collect/$', collect), #/poker/collect/?pid=n&sid=xxx, return {"votes":{"uid":"n","uid":"*",..}}
)
